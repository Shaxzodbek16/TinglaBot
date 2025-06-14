from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.bot.models.users import User

from app.core.models import BaseModel
from datetime import datetime
from sqlalchemy import BigInteger, ForeignKey, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Subscription(BaseModel):
    __tablename__ = "subscriptions"

    tg_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.tg_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        doc="Telegram ID of the subscribing user",
    )

    start_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), doc="Subscription start timestamp"
    )
    end_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, doc="Subscription expiry timestamp"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, doc="Indicates if subscription is currently active"
    )

    user: Mapped[User] = relationship(
        "User", back_populates="subscription", uselist=False
    )

    def __repr__(self) -> str:
        return (
            f"<Subscription user_id={self.tg_id!r} "
            f"active={self.is_active} "
            f"until={self.end_date.isoformat()}>"
        )
