"""Modelo de datos — Fase 1 MVP."""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(String(200))
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True)


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    institution: Mapped[str] = mapped_column(String(60))
    # debito | credito | inversion | efectivo
    kind: Mapped[str] = mapped_column(String(20))
    currency: Mapped[str] = mapped_column(String(3), default="MXN")
    last4: Mapped[str] = mapped_column(String(8), default="")
    cut_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pay_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # saldo (para débito/inversión: saldo; crédito: no se usa como patrimonio)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    balance_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    in_networth: Mapped[bool] = mapped_column(Boolean, default=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str] = mapped_column(Text, default="")

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)
    emoji: Mapped[str] = mapped_column(String(8), default="")
    # ingreso | fijo | variable | aprovisionamiento | inversion | transferencia
    kind: Mapped[str] = mapped_column(String(20), default="variable")
    monthly_budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    sort: Mapped[int] = mapped_column(Integer, default=100)


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    date: Mapped[date] = mapped_column(Date, index=True)
    description: Mapped[str] = mapped_column(String(300))
    # positivo siempre; direction distingue cargo/abono
    amount: Mapped[float] = mapped_column(Float)
    direction: Mapped[str] = mapped_column(String(6))  # cargo | abono
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    tags: Mapped[str] = mapped_column(String(120), default="")  # csv: bebe,viaje,facturable
    source: Mapped[str] = mapped_column(String(20), default="manual")  # manual | import
    external_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    import_batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batches.id"), nullable=True)
    factura_status: Mapped[str] = mapped_column(String(15), default="")  # '' | pendiente | facturado | no_facturable
    notes: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    account: Mapped[Account] = relationship(back_populates="transactions")
    category: Mapped[Category | None] = relationship()


class MsiPlan(Base):
    __tablename__ = "msi_plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    merchant: Mapped[str] = mapped_column(String(120))
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_amount: Mapped[float] = mapped_column(Float)
    months: Mapped[int] = mapped_column(Integer)
    monthly_payment: Mapped[float] = mapped_column(Float)
    payments_made: Mapped[int] = mapped_column(Integer, default=0)
    # AAAA-MM de la primera mensualidad
    first_month: Mapped[str] = mapped_column(String(7))
    status: Mapped[str] = mapped_column(String(12), default="activo")  # activo | liquidado
    external_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    account: Mapped[Account] = relationship()


class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="MXN")
    frequency: Mapped[str] = mapped_column(String(10), default="mensual")  # mensual | anual
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    next_renewal: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(12), default="activa")  # activa | cancelada | por_confirmar
    notes: Mapped[str] = mapped_column(Text, default="")

    account: Mapped[Account | None] = relationship()


class Goal(Base):
    __tablename__ = "goals"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    emoji: Mapped[str] = mapped_column(String(8), default="🎯")
    target_amount: Mapped[float] = mapped_column(Float)
    current_amount: Mapped[float] = mapped_column(Float, default=0.0)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")


class Provision(Base):
    """Gasto anual aprovisionado a 1/12 mensual (seguros, predial, tenencia...)."""
    __tablename__ = "provisions"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    annual_amount: Mapped[float] = mapped_column(Float)
    due_months: Mapped[str] = mapped_column(String(30), default="")  # "01,05" meses en que se paga
    notes: Mapped[str] = mapped_column(Text, default="")


class ImportBatch(Base):
    __tablename__ = "import_batches"
    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(200))
    bank: Mapped[str] = mapped_column(String(30))
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    n_imported: Mapped[int] = mapped_column(Integer, default=0)
    n_skipped: Mapped[int] = mapped_column(Integer, default=0)
    reconciled: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
