from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (UniqueConstraint("external_id", "source", name="uq_customer_external_source"),)

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    activities = relationship("Activity", back_populates="customer")


class Activity(Base):
    __tablename__ = "activities"
    __table_args__ = (UniqueConstraint("external_id", "source", name="uq_activity_external_source"),)

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ai_summary = Column(Text, nullable=True)
    ai_category = Column(String(100), nullable=True)
    ai_priority = Column(String(50), nullable=True)

    customer = relationship("Customer", back_populates="activities")