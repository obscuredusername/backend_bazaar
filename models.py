from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db import Base

# User Table Model
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String,  nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    rating = Column(Float, default=0.0)
    joining_date = Column(DateTime, default=func.now())
    contact_no = Column(String, nullable=False)
    
    products = relationship("Product", back_populates="owner", cascade="all, delete")

# Product Table Model
class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    city = Column(String)
    location = Column(String)
    return_policy = Column(String)
    size = Column(String)  # Changed from ARRAY(String) to String
    images = Column(String)  # Store multiple image URLs as a comma-separated string
    type = Column(String)
    price = Column(Float, nullable=False)
    category = Column(String)
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # Ensure foreign key constraints
    
    owner = relationship("User", back_populates="products", lazy="joined")
