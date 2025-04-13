from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date

class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr
    contact_no: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    rating: float
    joining_date: date
    contact_no: str

    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    title: str
    description: str
    city: str
    location: str
    return_policy: str
    size: str  # Changed from dict to str
    images: List[str]  # List of image URLs
    type: str
    price: float
    category: str

class ProductResponse(BaseModel):
    id: int
    title: str
    images: List[str]  # List of image URLs
    category: str
    price: float
    type: str

    class Config:
        from_attributes = True

class ProductDetailResponse(BaseModel):
    title: str
    description: str
    city: str
    location: str
    return_policy: str
    size: str  # Changed from dict to str
    images: List[str]  # List of image URLs
    type: str
    price: float
    category: str
    user: UserResponse 

    class Config:
        from_attributes = True

class Login(BaseModel):
    email: EmailStr
    password: str
