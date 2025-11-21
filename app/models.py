import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .database import Base


def generate_uuid() -> str:
      return str(uuid.uuid4())


class User(Base):
      __tablename__ = "users"

      id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
      did: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
      username: Mapped[str | None] = mapped_column(String(100))
      email: Mapped[str | None] = mapped_column(String(150))
      created_at: Mapped[datetime] = mapped_column(
          DateTime, default=lambda: datetime.now(timezone.utc)
      )

      connectors: Mapped[list["Connector"]] = relationship(
          "Connector", back_populates="owner", cascade="all, delete-orphan"
      )


class DataSpace(Base):
      __tablename__ = "data_spaces"

      id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
      code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
      name: Mapped[str] = mapped_column(String(150), nullable=False)
      description: Mapped[str | None] = mapped_column(Text)

      connectors: Mapped[list["Connector"]] = relationship("Connector", back_populates="data_space")


class Connector(Base):
      __tablename__ = "connectors"

      id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
      did: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
      display_name: Mapped[str] = mapped_column(String(150), nullable=False)
      status: Mapped[str] = mapped_column(String(50), default="registered")
      did_document: Mapped[dict] = mapped_column(JSON, nullable=False)
      created_at: Mapped[datetime] = mapped_column(
          DateTime, default=lambda: datetime.now(timezone.utc)
      )

      owner_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
      data_space_id: Mapped[str] = mapped_column(String, ForeignKey("data_spaces.id"), nullable=False)

      owner: Mapped["User"] = relationship("User", back_populates="connectors")
      data_space: Mapped["DataSpace"] = relationship("DataSpace", back_populates="connectors")
      offerings: Mapped[list["DataOffering"]] = relationship(
          "DataOffering", back_populates="connector", cascade="all, delete-orphan"
      )
      provided_contracts: Mapped[list["Contract"]] = relationship(
          "Contract", back_populates="provider_connector", foreign_keys="Contract.provider_connector_id"
      )
      consumed_contracts: Mapped[list["Contract"]] = relationship(
          "Contract", back_populates="consumer_connector", foreign_keys="Contract.consumer_connector_id"
      )


class DataOffering(Base):
      __tablename__ = "data_offerings"

      id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
      title: Mapped[str] = mapped_column(String(150), nullable=False)
      description: Mapped[str] = mapped_column(Text, nullable=False)
      data_type: Mapped[str] = mapped_column(String(50), nullable=False)
      access_policy: Mapped[str] = mapped_column(String(50), nullable=False)
      storage_meta: Mapped[dict] = mapped_column(JSON, nullable=False)
      registration_status: Mapped[str] = mapped_column(String(50), default="unregistered")
      created_at: Mapped[datetime] = mapped_column(
          DateTime, default=lambda: datetime.now(timezone.utc)
      )

      connector_id: Mapped[str] = mapped_column(String, ForeignKey("connectors.id"), nullable=False)
      connector: Mapped["Connector"] = relationship("Connector", back_populates="offerings")


class Contract(Base):
      __tablename__ = "contracts"

      id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
      name: Mapped[str] = mapped_column(String(150), nullable=False)
      policy: Mapped[str] = mapped_column(String(100), nullable=False)
      status: Mapped[str] = mapped_column(String(50), default="active")
      contract_address: Mapped[str | None] = mapped_column(String(200))
      expires_at: Mapped[datetime | None] = mapped_column(DateTime)
      created_at: Mapped[datetime] = mapped_column(
          DateTime, default=lambda: datetime.now(timezone.utc)
      )

      provider_connector_id: Mapped[str] = mapped_column(
          String, ForeignKey("connectors.id"), nullable=False
      )
      consumer_connector_id: Mapped[str] = mapped_column(
          String, ForeignKey("connectors.id"), nullable=False
      )

      provider_connector: Mapped["Connector"] = relationship(
          "Connector", foreign_keys=[provider_connector_id], back_populates="provided_contracts"
      )
      consumer_connector: Mapped["Connector"] = relationship(
          "Connector", foreign_keys=[consumer_connector_id], back_populates="consumed_contracts"
      )