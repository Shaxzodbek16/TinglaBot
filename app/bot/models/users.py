from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.bot.models.statistics import Statistics
    from app.bot.models.referral import Referral
    from app.bot.models.subscription import Subscription

from app.core.models.base import BaseModelWithData
from sqlalchemy import BigInteger, Boolean, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property


class User(BaseModelWithData):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=False, unique=True, index=True
    )
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    username: Mapped[str | None] = mapped_column(
        String(32), nullable=True, unique=True, index=True
    )
    language_code: Mapped[str | None] = mapped_column(
        String(8), nullable=True, default=None
    )

    is_tg_premium: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    last_active: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        onupdate=datetime.now(),
        default=datetime.now(),
    )

    limit: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    # one-to-one relationship to Statistics
    statistics: Mapped["Statistics"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    # one-to-one relationship to Referral
    referral: Mapped["Referral"] = relationship(
        "Referral", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    subscription: Mapped["Subscription"] = relationship(
        "Subscription",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    @hybrid_property
    def full_name(self) -> str:
        # hybrid_property lets you filter/query on full_name too if needed
        return f"{self.first_name} {self.last_name or ''}".strip()

    def __repr__(self) -> str:
        return f"<User tg_id={self.tg_id!r} username={self.username!r}>"

    def get_referral_link(self, bot_username: str) -> str:
        """Return a deep-link referral URL for this user."""
        return f"https://t.me/{bot_username}?start={self.tg_id}"

    def is_active(self) -> bool:
        return self.last_active > datetime.now() - timedelta(days=30)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tg_id": self.tg_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "language_code": self.language_code,
            "is_tg_premium": self.is_tg_premium,
            "last_active": self.last_active,
            "limit": self.limit,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
