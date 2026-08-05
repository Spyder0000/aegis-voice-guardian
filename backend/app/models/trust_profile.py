"""Financial trust-profile persistence model."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import JSON, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TrustProfile(Base):
    __tablename__ = "trust_profile"

    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    known_recipients: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    recipient_transfer_counts: Mapped[dict[str, int]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    avg_transfer_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal(0), nullable=False
    )
    largest_transfer_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal(0), nullable=False
    )
    transfer_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False
    )

    ledger_entries: Mapped[list[TrustLedger]] = relationship(  # noqa: F821
        back_populates="profile"
    )
