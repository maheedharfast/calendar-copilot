from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import  relationship
from pkg.db_util.declarative_base import Base


class UserModel(Base):
    """SQLAlchemy model for User"""
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)

    # Relationship with UserAuth
    auth = relationship("UserAuthModel", back_populates="user", uselist=False)


class UserAuthModel(Base):
    """SQLAlchemy model for UserAuth"""
    __tablename__ = "user_auth"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    hashed_password = Column(String, nullable=False)

    # Relationship with User
    user = relationship("UserModel", back_populates="auth")