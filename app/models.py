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
      policy_templates: Mapped[list["PolicyTemplate"]] = relationship(
          "PolicyTemplate", back_populates="connector", cascade="all, delete-orphan"
      )
      contract_templates: Mapped[list["ContractTemplate"]] = relationship(
          "ContractTemplate", back_populates="connector", cascade="all, delete-orphan"
      )
      data_requests: Mapped[list["DataRequest"]] = relationship(
          "DataRequest", back_populates="consumer_connector"
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
      data_requests: Mapped[list["DataRequest"]] = relationship(
          "DataRequest", back_populates="data_offering"
      )
      contracts: Mapped[list["Contract"]] = relationship(
          "Contract", back_populates="data_offering"
      )


class PolicyRule(Base):
      __tablename__ = "policy_rules"

      id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
      type: Mapped[str] = mapped_column(String(50), nullable=False)
      name: Mapped[str] = mapped_column(String(150), nullable=False)
      description: Mapped[str] = mapped_column(Text, nullable=False)
      value: Mapped[str] = mapped_column(String(100), nullable=False)
      unit: Mapped[str | None] = mapped_column(String(50))
      is_active: Mapped[bool] = mapped_column(default=True)
      created_at: Mapped[datetime] = mapped_column(
          DateTime, default=lambda: datetime.now(timezone.utc)
      )

      policy_template_id: Mapped[str] = mapped_column(
          String, ForeignKey("policy_templates.id"), nullable=False
      )

      policy_template: Mapped["PolicyTemplate"] = relationship(
          "PolicyTemplate", back_populates="rules"
      )


class PolicyTemplate(Base):
      __tablename__ = "policy_templates"

      id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
      name: Mapped[str] = mapped_column(String(150), nullable=False)
      description: Mapped[str] = mapped_column(Text, nullable=False)
      category: Mapped[str] = mapped_column(String(50), nullable=False)
      severity: Mapped[str] = mapped_column(String(20), nullable=False)
      enforcement_type: Mapped[str] = mapped_column(String(20), nullable=False)
      created_at: Mapped[datetime] = mapped_column(
          DateTime, default=lambda: datetime.now(timezone.utc)
      )
      updated_at: Mapped[datetime | None] = mapped_column(DateTime)

      connector_id: Mapped[str] = mapped_column(
          String, ForeignKey("connectors.id"), nullable=False
      )

      connector: Mapped["Connector"] = relationship("Connector", back_populates="policy_templates")
      rules: Mapped[list["PolicyRule"]] = relationship(
          "PolicyRule", back_populates="policy_template", cascade="all, delete-orphan"
      )
      contract_templates: Mapped[list["ContractTemplate"]] = relationship(
          "ContractTemplate", secondary="contract_template_policies", back_populates="policy_templates"
      )


class ContractTemplate(Base):
      __tablename__ = "contract_templates"

      id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
      name: Mapped[str] = mapped_column(String(150), nullable=False)
      description: Mapped[str] = mapped_column(Text, nullable=False)
      contract_type: Mapped[str] = mapped_column(String(20), nullable=False)
      status: Mapped[str] = mapped_column(String(20), default="draft")
      usage_count: Mapped[int] = mapped_column(default=0)
      created_at: Mapped[datetime] = mapped_column(
          DateTime, default=lambda: datetime.now(timezone.utc)
      )
      updated_at: Mapped[datetime | None] = mapped_column(DateTime)

      connector_id: Mapped[str] = mapped_column(
          String, ForeignKey("connectors.id"), nullable=False
      )

      connector: Mapped["Connector"] = relationship("Connector", back_populates="contract_templates")
      policy_templates: Mapped[list["PolicyTemplate"]] = relationship(
          "PolicyTemplate", secondary="contract_template_policies", back_populates="contract_templates"
      )
      contracts: Mapped[list["Contract"]] = relationship(
          "Contract", back_populates="contract_template"
      )


class ContractTemplatePolicy(Base):
      __tablename__ = "contract_template_policies"

      contract_template_id: Mapped[str] = mapped_column(
          String, ForeignKey("contract_templates.id"), primary_key=True
      )
      policy_template_id: Mapped[str] = mapped_column(
          String, ForeignKey("policy_templates.id"), primary_key=True
      )


class DataRequest(Base):
      __tablename__ = "data_requests"

      id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
      purpose: Mapped[str] = mapped_column(Text, nullable=False)
      access_mode: Mapped[str] = mapped_column(String(20), nullable=False)
      status: Mapped[str] = mapped_column(String(20), default="pending")
      created_at: Mapped[datetime] = mapped_column(
          DateTime, default=lambda: datetime.now(timezone.utc)
      )
      updated_at: Mapped[datetime | None] = mapped_column(DateTime)

      data_offering_id: Mapped[str] = mapped_column(
          String, ForeignKey("data_offerings.id"), nullable=False
      )
      consumer_connector_id: Mapped[str] = mapped_column(
          String, ForeignKey("connectors.id"), nullable=False
      )

      data_offering: Mapped["DataOffering"] = relationship("DataOffering", back_populates="data_requests")
      consumer_connector: Mapped["Connector"] = relationship("Connector", back_populates="data_requests")
      contract: Mapped["Contract | None"] = relationship("Contract", back_populates="data_request", uselist=False)


class Contract(Base):
      __tablename__ = "contracts"

      id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
      name: Mapped[str] = mapped_column(String(150), nullable=False)
      status: Mapped[str] = mapped_column(String(50), default="pending_consumer")
      contract_address: Mapped[str | None] = mapped_column(String(200))
      blockchain_tx_id: Mapped[str | None] = mapped_column(String(200))
      blockchain_network: Mapped[str] = mapped_column(String(50), default="Ethereum")
      expires_at: Mapped[datetime | None] = mapped_column(DateTime)
      created_at: Mapped[datetime] = mapped_column(
          DateTime, default=lambda: datetime.now(timezone.utc)
      )
      updated_at: Mapped[datetime | None] = mapped_column(DateTime)

      provider_connector_id: Mapped[str] = mapped_column(
          String, ForeignKey("connectors.id"), nullable=False
      )
      consumer_connector_id: Mapped[str] = mapped_column(
          String, ForeignKey("connectors.id"), nullable=False
      )
      contract_template_id: Mapped[str] = mapped_column(
          String, ForeignKey("contract_templates.id"), nullable=False
      )
      data_offering_id: Mapped[str] = mapped_column(
          String, ForeignKey("data_offerings.id"), nullable=False
      )
      data_request_id: Mapped[str | None] = mapped_column(
          String, ForeignKey("data_requests.id")
      )

      provider_connector: Mapped["Connector"] = relationship(
          "Connector", foreign_keys=[provider_connector_id], back_populates="provided_contracts"
      )
      consumer_connector: Mapped["Connector"] = relationship(
          "Connector", foreign_keys=[consumer_connector_id], back_populates="consumed_contracts"
      )
      contract_template: Mapped["ContractTemplate"] = relationship(
          "ContractTemplate", back_populates="contracts"
      )
      data_offering: Mapped["DataOffering"] = relationship(
          "DataOffering", back_populates="contracts"
      )
      data_request: Mapped["DataRequest | None"] = relationship(
          "DataRequest", back_populates="contract"
      )