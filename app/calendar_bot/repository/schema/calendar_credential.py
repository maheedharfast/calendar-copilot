from sqlalchemy import Column, String, JSON, DateTime
from pkg.db_util.declarative_base import Base
from datetime import datetime

class CalendarCredentialModel(Base):
    """SQLAlchemy model for Calendar Credentials"""
    __tablename__ = "calendar_credentials"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    credential = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
