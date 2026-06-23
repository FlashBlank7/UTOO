from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ActivationCode(Base):
    __tablename__ = "activation_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    max_uses: Mapped[int] = mapped_column(Integer, default=20)
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    usages = relationship("ActivationCodeUsage", back_populates="code", lazy="noload")


class ActivationCodeUsage(Base):
    __tablename__ = "activation_code_usages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code_id: Mapped[int] = mapped_column(Integer, ForeignKey("activation_codes.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    code = relationship("ActivationCode", back_populates="usages", lazy="noload")
    user = relationship("User", back_populates="code_usages", lazy="noload")
