from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func
from .database import Base

class DIDRecord(Base):
    __tablename__ = "did_records"

    did = Column(String, primary_key=True, index=True)
    document = Column(Text, nullable=False)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "users"

    did = Column(String, primary_key=True, index=True)
    did_document = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())