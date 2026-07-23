from __future__ import annotations

from decimal import Decimal
from typing import cast

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.models import Booking
from app.adapters.persistence.sqlalchemy.models import Payment
from app.adapters.persistence.sqlalchemy.models import User
from app.adapters.persistence.sqlalchemy.models import WalletTransaction
from app.adapters.persistence.sqlalchemy.models.common import generate_uuid
from app.dto.commerce import AdminPaymentStatusPayload
from app.dto.commerce import BookingPaymentPayload
from app.dto.commerce import BookingPaymentQuoteOut
from app.dto.commerce import PaymentOut
from app.dto.commerce import PaymentMethod
from app.dto.commerce import PaymentStatus
from app.dto.commerce import PaymentType
from app.dto.commerce import WalletOut
from app.dto.commerce import WalletDirection
from app.dto.commerce import WalletTopUpPayload
from app.dto.commerce import WalletTransactionOut
from app.dto.commerce import WalletTransactionType
from app.entrypoints.api.dependencies import CurrentUser
from app.entrypoints.api.dependencies import get_current_admin
from app.entrypoints.api.dependencies import get_current_customer
from app.adapters.persistence.sqlalchemy.session import get_db
from app.shared.errors import BadRequestError
from app.shared.errors import ConflictError
from app.shared.errors import ForbiddenError
from app.shared.errors import NotFoundError


router = APIRouter(tags=["commerce"])


def _payment_to_dto(payment: Payment) -> PaymentOut:
    return PaymentOut(
        id=payment.id,
        booking_id=payment.booking_id,
        user_id=payment.user_id,
        method=cast(PaymentMethod, payment.method),
        status=cast(PaymentStatus, payment.status),
        amount=float(payment.amount),
        type=cast(PaymentType, payment.payment_type),
        reference=payment.reference,
        note=payment.note,
        created_at=payment.created_at.isoformat(),
    )


def _wallet_transactions(db: Session, user_id: str) -> list[WalletTransaction]:
    return list(
        db.execute(
            select(WalletTransaction)
            .where(WalletTransaction.user_id == user_id)
            .order_by(WalletTransaction.created_at.desc())
        )
        .scalars()
        .all()
    )


def _wallet_balance(transactions: list[WalletTransaction]) -> Decimal:
    return sum(
        (
            item.amount if item.direction == "credit" else -item.amount
            for item in transactions
        ),
        Decimal("0"),
    )


def _wallet_transaction_to_dto(
    transaction: WalletTransaction,
) -> WalletTransactionOut:
    return WalletTransactionOut(
        id=transaction.id,
        user_id=transaction.user_id,
        type=cast(WalletTransactionType, transaction.transaction_type),
        direction=cast(WalletDirection, transaction.direction),
        status="completed",
        amount=float(transaction.amount),
        description=transaction.description,
        created_at=transaction.created_at.isoformat(),
        related_booking_id=transaction.related_booking_id,
        method_label=transaction.method_label,
    )


def _booking_amount(booking: Booking) -> Decimal:
    inventory = booking.string_item.inventory_item
    if (
        inventory is None
        or inventory.pricing_mode != "fixed_price"
        or inventory.selling_price is None
        or inventory.selling_price <= 0
    ):
        raise BadRequestError("This booking still requires a shop-confirmed price")
    return Decimal(inventory.selling_price).quantize(Decimal("0.01"))


@router.get("/payments", response_model=list[PaymentOut])
def list_my_payments(
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> list[PaymentOut]:
    payments = db.execute(
        select(Payment)
        .where(Payment.user_id == current_user.user_id)
        .order_by(Payment.created_at.desc())
    ).scalars()
    return [_payment_to_dto(payment) for payment in payments]


@router.get(
    "/payments/bookings/{booking_id}/quote",
    response_model=BookingPaymentQuoteOut,
)
def get_booking_payment_quote(
    booking_id: str,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> BookingPaymentQuoteOut:
    booking = db.execute(
        select(Booking).where(Booking.id == booking_id)
    ).scalar_one_or_none()
    if booking is None:
        raise NotFoundError("Booking not found")
    if booking.user_id != current_user.user_id:
        raise ForbiddenError("Booking belongs to another user")

    active_payment = db.execute(
        select(Payment)
        .where(
            Payment.booking_id == booking.id,
            Payment.status.in_(["pending", "paid"]),
        )
        .order_by(Payment.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    amount = (
        active_payment.amount
        if active_payment is not None
        else _booking_amount(booking)
    )
    wallet_balance = _wallet_balance(_wallet_transactions(db, current_user.user_id))

    return BookingPaymentQuoteOut(
        booking_id=booking.id,
        string_fee=float(amount),
        service_fee=0,
        total_amount=float(amount),
        wallet_balance=float(wallet_balance),
        active_payment=_payment_to_dto(active_payment)
        if active_payment is not None
        else None,
    )


@router.post("/payments/bookings/{booking_id}", response_model=PaymentOut)
def create_booking_payment(
    booking_id: str,
    payload: BookingPaymentPayload,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> PaymentOut:
    booking = db.execute(
        select(Booking).where(Booking.id == booking_id).with_for_update()
    ).scalar_one_or_none()
    if booking is None:
        raise NotFoundError("Booking not found")
    if booking.user_id != current_user.user_id:
        raise ForbiddenError("Booking belongs to another user")

    active_payment = db.execute(
        select(Payment).where(
            Payment.booking_id == booking.id,
            Payment.status.in_(["pending", "paid"]),
        )
    ).scalar_one_or_none()
    if active_payment is not None:
        return _payment_to_dto(active_payment)

    amount = _booking_amount(booking)
    if payload.expected_amount is not None:
        expected_amount = Decimal(str(payload.expected_amount)).quantize(
            Decimal("0.01")
        )
        if expected_amount != amount:
            raise ConflictError("Booking price changed; refresh the payment quote")
    status = "pending"
    note = "Awaiting shop verification of the external payment."
    payment_id = generate_uuid()
    payment = Payment(
        id=payment_id,
        booking_id=booking.id,
        user_id=current_user.user_id,
        method=payload.method,
        status=status,
        amount=amount,
        payment_type="booking_payment",
        reference=f"PAY-{payment_id[:8].upper()}",
        note=note,
    )
    db.add(payment)
    if payload.method == "wallet_balance":
        db.execute(
            select(User.id).where(User.id == current_user.user_id).with_for_update()
        ).scalar_one()
        transactions = _wallet_transactions(db, current_user.user_id)
        if _wallet_balance(transactions) < amount:
            db.rollback()
            raise BadRequestError("Wallet balance is insufficient")
        payment.status = "paid"
        payment.note = "Paid from persisted wallet balance."
        db.add(
            WalletTransaction(
                user_id=current_user.user_id,
                payment_id=payment.id,
                transaction_type="booking_payment",
                direction="debit",
                amount=amount,
                description=f"Wallet payment for {booking.id}",
                method_label="Wallet balance",
                related_booking_id=booking.id,
            )
        )

    db.commit()
    db.refresh(payment)
    return _payment_to_dto(payment)


@router.get("/wallet", response_model=WalletOut)
def get_wallet(
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> WalletOut:
    transactions = _wallet_transactions(db, current_user.user_id)
    pending_top_up = db.execute(
        select(Payment).where(
            Payment.user_id == current_user.user_id,
            Payment.payment_type == "wallet_top_up",
            Payment.status == "pending",
        )
    ).scalars()
    pending_total = sum((item.amount for item in pending_top_up), Decimal("0"))
    lifetime_top_ups = sum(
        (
            item.amount
            for item in transactions
            if item.transaction_type == "top_up" and item.direction == "credit"
        ),
        Decimal("0"),
    )
    return WalletOut(
        user_id=current_user.user_id,
        available_balance=float(_wallet_balance(transactions)),
        pending_top_up=float(pending_total),
        lifetime_top_ups=float(lifetime_top_ups),
        transactions=[_wallet_transaction_to_dto(item) for item in transactions],
    )


@router.post("/wallet/top-ups", response_model=PaymentOut)
def request_wallet_top_up(
    payload: WalletTopUpPayload,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> PaymentOut:
    payment_id = generate_uuid()
    payment = Payment(
        id=payment_id,
        user_id=current_user.user_id,
        method=payload.method,
        status="pending",
        amount=Decimal(str(payload.amount)).quantize(Decimal("0.01")),
        payment_type="wallet_top_up",
        reference=f"TOP-{payment_id[:8].upper()}",
        note="Awaiting admin verification before wallet credit.",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return _payment_to_dto(payment)


@router.get("/admin/payments", response_model=list[PaymentOut])
def admin_list_payments(
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[PaymentOut]:
    payments = db.execute(select(Payment).order_by(Payment.created_at.desc())).scalars()
    return [_payment_to_dto(payment) for payment in payments]


@router.patch("/admin/payments/{payment_id}", response_model=PaymentOut)
def admin_update_payment(
    payment_id: str,
    payload: AdminPaymentStatusPayload,
    _: CurrentUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> PaymentOut:
    payment = db.execute(
        select(Payment).where(Payment.id == payment_id).with_for_update()
    ).scalar_one_or_none()
    if payment is None:
        raise NotFoundError("Payment not found")
    if payment.status == payload.status:
        return _payment_to_dto(payment)
    if payment.status != "pending":
        raise ConflictError("Only pending payments can be updated")

    payment.status = payload.status
    if payload.status == "paid":
        payment.note = "Payment verified by the shop admin."
        if payment.payment_type == "wallet_top_up":
            db.add(
                WalletTransaction(
                    user_id=payment.user_id,
                    payment_id=payment.id,
                    transaction_type="top_up",
                    direction="credit",
                    amount=payment.amount,
                    description="Wallet top-up verified by the shop.",
                    method_label=payment.method.replace("_", " ").title(),
                )
            )
    else:
        payment.note = f"Payment marked {payload.status} by the shop admin."

    db.commit()
    db.refresh(payment)
    return _payment_to_dto(payment)
