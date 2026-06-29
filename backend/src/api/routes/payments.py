"""
Payments API Router
"""

from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_db
from src.domain.models import (
    Payment,
    PaymentStatus,
    PaymentProvider,
    User,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
)
from src.api.schemas.payment import (
    PaymentResponse,
    PaymentCreate,
    PaymentListResponse,
    PaymentInitResponse,
    PaymentWebhook,
    PaymentStatsResponse,
    PaymentProviderInfo,
    PaymentProvidersResponse,
)
from src.api.dependencies.auth import get_current_active_user, get_current_admin_user, verify_api_key
from src.core.config import settings

router = APIRouter()


@router.get("/", response_model=PaymentListResponse)
async def get_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[PaymentStatus] = None,
    provider: Optional[PaymentProvider] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Get all payments (Admin only)
    """
    query = select(Payment)
    
    if status_filter:
        query = query.where(Payment.status == status_filter)
    if provider:
        query = query.where(Payment.provider == provider)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Get payments with pagination
    query = query.offset(skip).limit(limit).order_by(Payment.created_at.desc())
    result = await db.execute(query)
    payments = result.scalars().all()
    
    return PaymentListResponse(
        items=payments,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/my", response_model=List[PaymentResponse])
async def get_my_payments(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Get current user's payments
    """
    query = select(Payment).where(
        Payment.user_id == user.id
    ).order_by(Payment.created_at.desc())
    
    result = await db.execute(query)
    payments = result.scalars().all()
    
    return payments


@router.get("/providers", response_model=PaymentProvidersResponse)
async def get_payment_providers():
    """
    Get available payment providers
    """
    providers = []
    
    if settings.STRIPE_ENABLED and settings.STRIPE_SECRET_KEY:
        providers.append(PaymentProviderInfo(
            provider=PaymentProvider.STRIPE,
            name="Credit/Debit Card",
            enabled=True,
            supported_currencies=["USD", "EUR", "GBP"],
            min_amount=1.0,
            max_amount=10000.0,
        ))
    
    if settings.CRYPTO_ENABLED and settings.CRYPTO_API_KEY:
        providers.append(PaymentProviderInfo(
            provider=PaymentProvider.CRYPTO,
            name="Cryptocurrency",
            enabled=True,
            supported_currencies=["BTC", "ETH", "USDT", "LTC"],
            min_amount=5.0,
            max_amount=50000.0,
        ))
    
    if settings.YOOKASSA_ENABLED and settings.YOOKASSA_SECRET_KEY:
        providers.append(PaymentProviderInfo(
            provider=PaymentProvider.YOOKASSA,
            name="ЮKassa",
            enabled=True,
            supported_currencies=["RUB"],
            min_amount=100.0,
            max_amount=1000000.0,
        ))
    
    if settings.TELEGRAM_PAYMENT_TOKEN:
        providers.append(PaymentProviderInfo(
            provider=PaymentProvider.TELEGRAM,
            name="Telegram Stars",
            enabled=True,
            supported_currencies=["XTR"],
            min_amount=1.0,
            max_amount=10000.0,
        ))
    
    return PaymentProvidersResponse(providers=providers)


@router.post("/create", response_model=PaymentInitResponse)
async def create_payment(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Create new payment and get checkout URL
    """
    # Validate plan and get price
    plan_prices = {
        SubscriptionPlan.MONTH_1: settings.PLAN_1_MONTH_PRICE,
        SubscriptionPlan.MONTHS_3: settings.PLAN_3_MONTHS_PRICE,
        SubscriptionPlan.MONTHS_6: settings.PLAN_6_MONTHS_PRICE,
        SubscriptionPlan.MONTHS_12: settings.PLAN_12_MONTHS_PRICE,
        SubscriptionPlan.LIFETIME: settings.PLAN_LIFETIME_PRICE,
    }
    
    amount = plan_prices.get(payment_data.plan)
    if amount is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subscription plan"
        )
    
    # Apply promo code if provided
    if payment_data.promo_code:
        # TODO: Apply promo code discount
        pass
    
    # Create payment record
    payment = Payment(
        user_id=user.id,
        amount=amount,
        currency=payment_data.currency,
        status=PaymentStatus.PENDING,
        provider=payment_data.provider,
        description=payment_data.description or f"Subscription: {payment_data.plan.value}",
        metadata={"plan": payment_data.plan.value, "promo_code": payment_data.promo_code}
    )
    
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    
    # Initialize payment with provider
    checkout_url = ""
    invoice_id = None
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    if payment_data.provider == PaymentProvider.STRIPE:
        checkout_url, invoice_id = await _create_stripe_payment(payment, user)
    elif payment_data.provider == PaymentProvider.CRYPTO:
        checkout_url, invoice_id = await _create_crypto_payment(payment, user)
    elif payment_data.provider == PaymentProvider.YOOKASSA:
        checkout_url, invoice_id = await _create_yookassa_payment(payment, user)
    elif payment_data.provider == PaymentProvider.TELEGRAM:
        checkout_url, invoice_id = await _create_telegram_payment(payment, user)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment provider not supported"
        )
    
    # Update payment with external IDs
    payment.external_id = invoice_id
    payment.invoice_id = invoice_id
    await db.commit()
    
    return PaymentInitResponse(
        payment_id=payment.id,
        checkout_url=checkout_url,
        invoice_id=invoice_id,
        amount=amount,
        currency=payment_data.currency,
        expires_at=expires_at,
    )


@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Stripe webhook handler
    """
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            await _handle_successful_payment(session['id'], db)
        
        return {"status": "success"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/webhook/crypto")
async def crypto_webhook(
    webhook_data: PaymentWebhook,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """
    Crypto payment webhook handler
    """
    await _handle_payment_webhook(webhook_data, db)
    return {"status": "success"}


@router.post("/webhook/yookassa")
async def yookassa_webhook(
    webhook_data: PaymentWebhook,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """
    ЮKassa webhook handler
    """
    await _handle_payment_webhook(webhook_data, db)
    return {"status": "success"}


@router.get("/stats", response_model=PaymentStatsResponse)
async def get_payment_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Get payment statistics (Admin only)
    """
    query = select(Payment)
    result = await db.execute(query)
    payments = result.scalars().all()
    
    total_payments = len(payments)
    successful_payments = sum(1 for p in payments if p.status == PaymentStatus.COMPLETED)
    failed_payments = sum(1 for p in payments if p.status == PaymentStatus.FAILED)
    pending_payments = sum(1 for p in payments if p.status == PaymentStatus.PENDING)
    
    total_revenue = sum(p.amount for p in payments if p.status == PaymentStatus.COMPLETED)
    
    # Revenue by plan
    revenue_by_plan = {}
    for payment in payments:
        if payment.status == PaymentStatus.COMPLETED and payment.metadata:
            plan = payment.metadata.get('plan', 'unknown')
            revenue_by_plan[plan] = revenue_by_plan.get(plan, 0) + payment.amount
    
    # Revenue by provider
    revenue_by_provider = {}
    for payment in payments:
        if payment.status == PaymentStatus.COMPLETED:
            provider = payment.provider.value
            revenue_by_provider[provider] = revenue_by_provider.get(provider, 0) + payment.amount
    
    # Today's revenue
    today = datetime.utcnow().date()
    today_revenue = sum(
        p.amount for p in payments
        if p.status == PaymentStatus.COMPLETED and p.completed_at and p.completed_at.date() == today
    )
    
    # This month's revenue
    this_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_revenue = sum(
        p.amount for p in payments
        if p.status == PaymentStatus.COMPLETED and p.completed_at and p.completed_at >= this_month
    )
    
    return PaymentStatsResponse(
        total_revenue=total_revenue,
        total_payments=total_payments,
        successful_payments=successful_payments,
        failed_payments=failed_payments,
        pending_payments=pending_payments,
        revenue_by_plan=revenue_by_plan,
        revenue_by_provider=revenue_by_provider,
        today_revenue=today_revenue,
        this_month_revenue=this_month_revenue,
    )


# ============================================================================
# PAYMENT PROVIDER INTEGRATIONS
# ============================================================================

async def _create_stripe_payment(payment: Payment, user: User) -> tuple[str, str]:
    """Create Stripe checkout session"""
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': payment.currency.lower(),
                    'product_data': {
                        'name': 'GHETTO VPN Subscription',
                        'description': payment.description,
                    },
                    'unit_amount': int(payment.amount * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{settings.ADMIN_PANEL_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.ADMIN_PANEL_URL}/payment/cancel",
            client_reference_id=str(user.id),
            metadata={
                'payment_id': str(payment.id),
                'user_id': str(user.id),
            }
        )
        
        return session.url, session.id
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe error: {str(e)}"
        )


async def _create_crypto_payment(payment: Payment, user: User) -> tuple[str, str]:
    """Create crypto payment invoice"""
    # TODO: Integrate with CryptoCloud or CryptoBot
    invoice_url = f"https://crypto.example.com/invoice/{payment.id}"
    invoice_id = f"crypto_{payment.id}"
    return invoice_url, invoice_id


async def _create_yookassa_payment(payment: Payment, user: User) -> tuple[str, str]:
    """Create ЮKassa payment"""
    # TODO: Integrate with ЮKassa API
    payment_url = f"https://yookassa.ru/payment/{payment.id}"
    payment_id = f"yookassa_{payment.id}"
    return payment_url, payment_id


async def _create_telegram_payment(payment: Payment, user: User) -> tuple[str, str]:
    """Create Telegram Stars payment"""
    # This is handled directly in Telegram bot
    payment_url = f"https://t.me/{settings.BOT_TOKEN.split(':')[0]}"
    invoice_id = f"tg_{payment.id}"
    return payment_url, invoice_id


async def _handle_successful_payment(external_id: str, db: AsyncSession):
    """Handle successful payment and activate subscription"""
    # Find payment
    query = select(Payment).where(Payment.external_id == external_id)
    result = await db.execute(query)
    payment = result.scalar_one_or_none()
    
    if not payment:
        return
    
    # Update payment status
    payment.status = PaymentStatus.COMPLETED
    payment.completed_at = datetime.utcnow()
    
    # Get user
    query = select(User).where(User.id == payment.user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        return
    
    # Get plan from metadata
    plan_str = payment.metadata.get('plan') if payment.metadata else None
    if not plan_str:
        return
    
    plan = SubscriptionPlan(plan_str)
    
    # Calculate subscription duration
    plan_durations = {
        SubscriptionPlan.MONTH_1: 30,
        SubscriptionPlan.MONTHS_3: 90,
        SubscriptionPlan.MONTHS_6: 180,
        SubscriptionPlan.MONTHS_12: 365,
        SubscriptionPlan.LIFETIME: 36500,
    }
    
    duration_days = plan_durations.get(plan, 30)
    
    # Create or extend subscription
    start_date = datetime.utcnow()
    if user.subscription_end and user.subscription_end > start_date:
        start_date = user.subscription_end
    
    end_date = start_date + timedelta(days=duration_days)
    
    subscription = Subscription(
        user_id=user.id,
        plan=plan,
        status=SubscriptionStatus.ACTIVE,
        start_date=start_date,
        end_date=end_date,
        price=payment.amount,
        currency=payment.currency,
        payment_id=payment.id,
        promo_code=payment.metadata.get('promo_code') if payment.metadata else None,
    )
    
    db.add(subscription)
    
    # Update user
    user.is_premium = True
    user.subscription_end = end_date
    
    # Link payment to subscription
    await db.commit()
    await db.refresh(subscription)
    
    payment.metadata = payment.metadata or {}
    payment.metadata['subscription_id'] = subscription.id
    
    await db.commit()
    
    # TODO: Send notification to user


async def _handle_payment_webhook(webhook_data: PaymentWebhook, db: AsyncSession):
    """Generic webhook handler"""
    await _handle_successful_payment(webhook_data.external_id, db)
