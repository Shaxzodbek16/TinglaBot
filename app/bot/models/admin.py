from sqlalchemy.sql.sqltypes import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import BaseModel


class AdminRequirements(BaseModel):
    __tablename__ = "admin_requirements"

    token_per_referral: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=10
    )

    def __repr__(self) -> str:
        return f"<AdminRequirements token_per_referral={self.token_per_referral!r}>"
