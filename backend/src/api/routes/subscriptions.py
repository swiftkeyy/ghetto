"""
Subscriptions API Router
"""

from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_db
from src.domain.models import (
    Subscription,
    SubscriptionStatus,
    SubscriptionPlan,
    User,
    PromoCode,
)
from src.api.schemas.subscription import (
    SubscriptionResponse,
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionListResponse,
    SubscriptionExtend,
    SubscriptionPlanInfo,
    SubscriptionPlansResponse,
)
from src.api.dependencies.auth import get_current_active_user, get_current_admin_user
from src.core.config import settings

router = APIRouter()


@router.get("/", response_model=SubscriptionListResponse)
async def get_subscriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[SubscriptionStatus] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Get all subscriptions (Admin only)
    """
    query = select(Subscription)
    
    if status_filter:
        query = query.where(Subscription.status == status_filter)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Get subscriptions with pagination
    query = query.offset(skip).limit(limit).order_by(Subscription.created_at.desc())
    result = await db.execute(query)
    subscriptions = result.scalars().all()
    
    return SubscriptionListResponse(
        items=subscriptions,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/my", response_model=List[SubscriptionResponse])
async def get_my_subscriptions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Get current user's subscriptions
    """
    query = select(Subscription).where(
        Subscription.user_id == user.id
    ).order_by(Subscription.created_at.desc())
    
    result = await db.execute(query)
    subscriptions = result.scalars().all()
    
    return subscriptions


@router.get("/plans", response_model=SubscriptionPlansResponse)
async def get_subscription_plans():
    """
    Get available subscription plans
    """
    plans = [
        SubscriptionPlanInfo(
            plan=SubscriptionPlan.TRIAL,
            name="Trial",
            duration_days=settings.TRIAL_DAYS,
            price=0.0,
            currency="USD",
            features=[
                "3 дня бесплатно",
                "До 10 GB трафика",
                "Доступ ко всем серверам",
                "Все премиум функции"
            ],
            is_popular=False,
        ),
        SubscriptionPlanInfo(
            plan=SubscriptionPlan.MONTH_1,
            name="1 месяц",
            duration_days=30,
            price=settings.PLAN_1_MONTH_PRICE,
            currency="USD",
            features=[
                "Безлимитный трафик",
                "Максимальная скорость",
                "До 5 устройств",
                "Приоритетная поддержка"
            ],
            is_popular=False,
        ),
        SubscriptionPlanInfo(
            plan=SubscriptionPlan.MONTHS_3,
            name="3 месяца",
            duration_days=90,
            price=settings.PLAN_3_MONTHS_PRICE,
            currency="USD",
            discount_percent=17,
            features=[
                "Все функции 1 месяца",
                "Скидка 17%",
                "Экономия $5.00"
            ],
            is_popular=False,
        ),
        SubscriptionPlanInfo(
            plan=SubscriptionPlan.MONTHS_6,
            name="6 месяцев",
            duration_days=180,
            price=settings.PLAN_6_MONTHS_PRICE,
            currency="USD",
            discount_percent=25,
            features=[
                "Все функции 1 месяца",
                "Скидка 25%",
                "Экономия $15.00"
            ],
            is_popular=False,
        ),
        SubscriptionPlanInfo(
            plan=SubscriptionPlan.MONTHS_12,
            name="12 месяцев",
            duration_days=365,
            price=settings.PLAN_12_MONTHS_PRICE,
            currency="USD",
            discount_percent=33,
            features=[
                "Все функции 1 месяца",
                "Скидка 33%",
                "Экономия $40.00",
                "Лучшее предложение!"
            ],
            is_popular=True,
        ),
        SubscriptionPlanInfo(
            plan=SubscriptionPlan.LIFETIME,
            name="Навсегда",
            duration_days=36500,  # 100 years
            price=settings.PLAN_LIFETIME_PRICE,
            currency="USD",
            features=[
                "Пожизненный доступ",
                "Все будущие обновления",
                "VIP поддержка",
                "Максимальная выгода"
            ],
            is_popular=False,
        ),
    ]
    
    return SubscriptionPlansResponse(
        plans=plans,
        trial_available=settings.TRIAL_ENABLED,
        trial_days=settings.TRIAL_DAYS,
    )


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Get subscription by ID
    """
    query = select(Subscription).where(Subscription.id == subscription_id)
    result = await db.execute(query)
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Check ownership (non-admin)
    if not user.is_admin and subscription.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return subscription


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Create subscription manually (Admin only)
    """
    # Validate user exists
    query = select(User).where(User.id == subscription_data.user_id)
    result = await db.execute(query)
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create subscription
    subscription = Subscription(**subscription_data.model_dump())
    db.add(subscription)
    
    # Update user premium status
    target_user.is_premium = True
    target_user.subscription_end = subscription.end_date
    
    await db.commit()
    await db.refresh(subscription)
    
    return subscription


@router.post("/activate-trial", response_model=SubscriptionResponse)
async def activate_trial(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Activate trial subscription
    """
    if not settings.TRIAL_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trial is not available"
        )
    
    if user.trial_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trial already used"
        )
    
    # Create trial subscription
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=settings.TRIAL_DAYS)
    
    subscription = Subscription(
        user_id=user.id,
        plan=SubscriptionPlan.TRIAL,
        status=SubscriptionStatus.ACTIVE,
        start_date=start_date,
        end_date=end_date,
        price=0.0,
        currency="USD",
    )
    
    db.add(subscription)
    
    # Update user
    user.trial_used = True
    user.trial_start = start_date
    user.trial_end = end_date
    user.is_premium = True
    user.subscription_end = end_date
    user.status = "trial"
    
    await db.commit()
    await db.refresh(subscription)
    
    return subscription


@router.patch("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    subscription_data: SubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Update subscription (Admin only)
    """
    query = select(Subscription).where(Subscription.id == subscription_id)
    result = await db.execute(query)
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Update fields
    for field, value in subscription_data.model_dump(exclude_unset=True).items():
        setattr(subscription, field, value)
    
    await db.commit()
    await db.refresh(subscription)
    
    return subscription


@router.post("/{subscription_id}/extend", response_model=SubscriptionResponse)
async def extend_subscription(
    subscription_id: int,
    extend_data: SubscriptionExtend,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Extend subscription by days (Admin only)
    """
    query = select(Subscription).where(Subscription.id == subscription_id)
    result = await db.execute(query)
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Extend end_date
    subscription.end_date = subscription.end_date + timedelta(days=extend_data.days)
    
    # Update user subscription_end
    query = select(User).where(User.id == subscription.user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user:
        user.subscription_end = subscription.end_date
    
    await db.commit()
    await db.refresh(subscription)
    
    return subscription


@router.post("/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Cancel subscription (turn off auto-renewal)
    """
    query = select(Subscription).where(Subscription.id == subscription_id)
    result = await db.execute(query)
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Check ownership
    if not user.is_admin and subscription.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    subscription.auto_renew = False
    subscription.status = SubscriptionStatus.CANCELLED
    
    await db.commit()
    
    return {
        "message": "Subscription cancelled successfully",
        "subscription_id": subscription_id,
        "valid_until": subscription.end_date
    }


@router.post("/apply-promo")
async def apply_promo_code(
    promo_code: str,
    plan: SubscriptionPlan,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Validate and calculate promo code discount
    """
    from src.domain.models import PromoCodeType
    
    query = select(PromoCode).where(
        PromoCode.code == promo_code.upper(),
        PromoCode.is_active == True,
    )
    result = await db.execute(query)
    promo = result.scalar_one_or_none()
    
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promo code not found or inactive"
        )
    
    # Check validity dates
    now = datetime.utcnow()
    if promo.valid_until and promo.valid_until < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Promo code expired"
        )
    
    if promo.valid_from > now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Promo code not yet valid"
        )
    
    # Check max uses
    if promo.max_uses and promo.current_uses >= promo.max_uses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Promo code usage limit reached"
        )
    
    # Get plan price
    plan_prices = {
        SubscriptionPlan.MONTH_1: settings.PLAN_1_MONTH_PRICE,
        SubscriptionPlan.MONTHS_3: settings.PLAN_3_MONTHS_PRICE,
        SubscriptionPlan.MONTHS_6: settings.PLAN_6_MONTHS_PRICE,
        SubscriptionPlan.MONTHS_12: settings.PLAN_12_MONTHS_PRICE,
        SubscriptionPlan.LIFETIME: settings.PLAN_LIFETIME_PRICE,
    }
    
    original_price = plan_prices.get(plan, 0.0)
    
    # Check min purchase amount
    if promo.min_purchase_amount and original_price < promo.min_purchase_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum purchase amount is ${promo.min_purchase_amount}"
        )
    
    # Calculate discount
    if promo.type == PromoCodeType.DISCOUNT_PERCENT:
        discount_amount = original_price * (promo.value / 100)
        final_price = original_price - discount_amount
    elif promo.type == PromoCodeType.DISCOUNT_AMOUNT:
        discount_amount = min(promo.value, original_price)
        final_price = original_price - discount_amount
    else:
        discount_amount = 0
        final_price = original_price
    
    return {
        "valid": True,
        "promo_code": promo.code,
        "type": promo.type.value,
        "original_price": original_price,
        "discount_amount": discount_amount,
        "final_price": max(0, final_price),
        "currency": "USD",
    }
