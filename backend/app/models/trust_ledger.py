"""Explainable trust-ledger persistence model."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TrustLedger(Base):
    __tablename__ = "trust_ledger"
    __table_args__ = (
        UniqueConstraint(
            "transaction_id", "action", name="uq_ledger_transaction_action"
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    transaction_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("trust_profile.user_id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    recipient: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    reasons: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    action: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, index=True, nullable=False
    )

    profile: Mapped[TrustProfile] = relationship(back_populates="ledger_entries")  # noqa: F821
