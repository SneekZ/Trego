from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, unique=True, index=True, nullable=False)
    lastName = Column(String, nullable=True)
    firstName = Column(String, nullable=True)

    refreshToken = Column(String, nullable=False)
    sessionToken = Column(String, unique=True, nullable=False)

    deleted = Column(Boolean, default=False)
    creationDate = Column(DateTime(timezone=True), server_default=func.now())