import datetime as dt
from typing import Optional, List

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    Text,
    TIMESTAMP,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class UserHub(Base):
    __tablename__ = "userhub"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(Text)
    tstart: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    balance: Mapped[Optional[int]] = mapped_column(
        Integer, server_default="0", nullable=False
    )
    is_reg: Mapped[bool] = mapped_column(
        Boolean, server_default="false", nullable=False
    )

    # self-reference
    refferer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("userhub.id", ondelete="SET NULL")
    )
    referrals: Mapped[List["UserHub"]] = relationship(
        back_populates="refferer", remote_side="UserHub.id"
    )
    refferer: Mapped[Optional["UserHub"]] = relationship(back_populates="referrals")

    # backrefs
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="user")
    pfuncs: Mapped[List["PFunc"]] = relationship(back_populates="user")
    tasks: Mapped[List["Task"]] = relationship(back_populates="user")
    spylogs: Mapped[List["SpyLog"]] = relationship(back_populates="user")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[Optional[str]] = mapped_column(Text)
    ts: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("userhub.id")
    )
    user: Mapped[Optional[UserHub]] = relationship(back_populates="transactions")


class PFunc(Base):
    __tablename__ = "pfunc"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    cls: Mapped[Optional[str]] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    ts: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    position: Mapped[Optional[str]] = mapped_column(Text)

    # FK
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("userhub.id"), nullable=False
    )
    pay_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transactions.id"), nullable=False
    )

    user: Mapped[UserHub] = relationship(back_populates="pfuncs")
    payment: Mapped[Transaction] = relationship()


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    test: Mapped[str] = mapped_column(Text, nullable=False)
    date: Mapped[dt.datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("userhub.id"), nullable=False
    )
    user: Mapped[UserHub] = relationship(back_populates="tasks")


class SpyLog(Base):
    """
    Обновлённая версия spylog:
      id       SERIAL PRIMARY KEY
      user_id  INT NOT NULL (FK → userhub)
      action   JSON/Text
      ts       TIMESTAMP NOT NULL
    """

    __tablename__ = "spylog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("userhub.id"), nullable=False
    )
    action: Mapped[dict] = mapped_column(JSON, nullable=False)
    ts: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=func.now(), nullable=False
    )

    user: Mapped[UserHub] = relationship(back_populates="spylogs")
