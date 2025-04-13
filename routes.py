from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import logging
from datetime import date
from datetime import datetime
from models import User, Product
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from schemas import (
    UserCreate, UserResponse, ProductResponse, 
    ProductDetailResponse, Login
)
from db import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

# Configure uploads
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_uploaded_file(file: UploadFile) -> str:
    """
    Save uploaded file and return the file path
    """
    # Create date-based subdirectory to prevent filename collisions
    today = datetime.now().strftime("%Y%m%d")
    upload_subdir = os.path.join(UPLOAD_DIR, today)
    os.makedirs(upload_subdir, exist_ok=True)

    # Generate unique filename
    timestamp = datetime.now().strftime("%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(upload_subdir, filename)

    return file_path

# Add direct file serving endpoint that keeps the original path format
@router.get("/uploads/{date_dir}/{filename}")
async def serve_image(date_dir: str, filename: str):
    """Serve image files directly from the uploads directory"""
    file_path = os.path.join(UPLOAD_DIR, date_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

@router.get("/all_users", response_model=List[UserResponse])
async def get_users(db: Session = Depends(get_db)):
    """Get all users"""
    try:
        users = db.query(User).all()
        logger.info(f"Retrieved {len(users)} users")
        return users
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving users"
        )

@router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    try:
        # Check if username exists
        existing_user = db.query(User).filter(User.username == user.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )

        # Check if email exists
        existing_email = db.query(User).filter(User.email == user.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        db_user = User(
            username=user.username,
            email=user.email,
            password=user.password,  # TODO: Add password hashing
            contact_no=user.contact_no
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"Created new user: {user.username}")
        return db_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )

@router.post("/products", response_model=ProductResponse)
async def create_product(
    title: str = Form(...),
    description: str = Form(...),
    city: str = Form(...),
    location: str = Form(...),
    return_policy: str = Form(...),
    size: str = Form(...),
    type: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    user_id: int = Form(...),
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Create a new product with images"""
    try:
        logger.info("Received product creation request")
        logger.info(f"Title: {title}")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Number of images: {len(images)}")

        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Validate images
        if not images:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one image is required"
            )

        # Process images
        image_paths = []
        for image in images:
            try:
                if not image.content_type.startswith('image/'):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"File {image.filename} is not an image"
                    )

                file_path = save_uploaded_file(image)
                with open(file_path, "wb") as f:
                    content = await image.read()
                    f.write(content)
                image_paths.append(file_path)
                logger.info(f"Saved image: {file_path}")

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error saving image {image.filename}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error saving image: {str(e)}"
                )

        # Convert image_paths to PostgreSQL array format
        images_pg_array = "{" + ",".join(image_paths) + "}"

        # Create product
        try:
            db_product = Product(
                title=title,
                description=description,
                city=city,
                location=location,
                return_policy=return_policy,
                size=size,
                type=type,
                price=float(price),
                category=category,
                user_id=int(user_id),
                images=images_pg_array  # Ensure correct array format
            )
            db.add(db_product)
            db.commit()
            db.refresh(db_product)
            
            logger.info(f"Created product: {db_product.id}")
            return db_product

        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid data format: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating product"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/products", response_model=List[ProductResponse])
async def get_products(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all products with pagination"""
    try:
        products = db.query(Product).offset(offset).limit(limit).all()

        # Process products to fix the image paths for frontend
        for product in products:
            if hasattr(product, 'images') and product.images:
                # Process PostgreSQL array format
                if isinstance(product.images, str):
                    images_str = product.images.strip('{}')
                    image_paths = [path.strip() for path in images_str.split(',') if path.strip()]
                else:
                    image_paths = product.images

                # Make paths appropriate for frontend (convert local paths to API URLs)
                api_paths = []
                for path in image_paths:
                    if path:
                        # Ensure we have the proper path for the API endpoint
                        # Extract the date dir and filename parts
                        parts = path.split('/')
                        
                        # Find the date directory and filename
                        # Looking for pattern like uploads/20250403/filename.jpg
                        if len(parts) >= 2:
                            # Check if parts[0] is 'uploads'
                            if parts[0] == 'uploads':
                                date_dir = parts[1]  # 20250403
                                filename = '/'.join(parts[2:])  # everything after date_dir
                                # Form the correct API URL path
                                api_paths.append(f"/uploads/{date_dir}/{filename}")
                            else:
                                # If 'uploads' is not in the path, use as is
                                api_paths.append(f"/uploads/{path}")
                        else:
                            # Fallback if path format is unexpected
                            api_paths.append(path)

                # Update the images attribute
                product.images = api_paths
                print(products)
        
        logger.info(f"Retrieved {len(products)} products")
        return products
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving products"
        )

@router.get("/products/{product_id}", response_model=ProductDetailResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get detailed product information"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        # Get user details
        user = db.query(User).filter(User.id == product.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Process images to make them accessible via API
        try:
            if isinstance(product.images, str):
                # Remove PostgreSQL array format characters and split
                images_str = product.images.strip('{}')
                image_paths = [path.strip() for path in images_str.split(',') if path.strip()]
            else:
                image_paths = product.images if product.images else []
            
            # Convert paths to API-accessible URLs
            api_paths = []
            for path in image_paths:
                if path:
                    # Similar path parsing as in get_products
                    parts = path.split('/')
                    
                    if len(parts) >= 2:
                        # Check if parts[0] is 'uploads'
                        if parts[0] == 'uploads':
                            date_dir = parts[1]  # 20250403
                            filename = '/'.join(parts[2:])  # everything after date_dir
                            # Form the correct API URL path
                            api_paths.append(f"/uploads/{date_dir}/{filename}")
                        else:
                            # If 'uploads' is not in the path, use as is
                            api_paths.append(f"/uploads/{path}")
                    else:
                        # Fallback if path format is unexpected
                        api_paths.append(path)
            
        except Exception as img_error:
            logger.error(f"Error processing images for product {product_id}: {str(img_error)}")
            api_paths = []

        return {
            "id": product.id,
            "title": product.title,
            "description": product.description,
            "price": product.price,
            "category": product.category,
            "type": product.type,
            "city": product.city,
            "location": product.location,
            "return_policy": product.return_policy,
            "size": product.size,
            "images": api_paths,  # API-accessible image paths
            "user": {
                "id": user.id,
                "username": user.username,
                "contact_no": user.contact_no,
                "rating": user.rating,
                "email": user.email,
                "joining_date": (
                    user.joining_date.strftime("%Y-%m-%d") 
                    if isinstance(user.joining_date, datetime) else None
                )
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving product"
        )    

@router.post("/signup", response_model=UserResponse)
async def signup(signup: UserCreate, db: Session = Depends(get_db)):
    """User sign-up with improved error handling"""
    try:
        # Input validation
        if not signup.email or not signup.password or not signup.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All fields are required"
            )

        # Check if email already exists
        if db.query(User).filter(User.email == signup.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check if username already exists
        if db.query(User).filter(User.username == signup.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create user with hashed password
        new_user = User(
            username=signup.username,
            email=signup.email,
            password=pwd_context.hash(signup.password),
            joining_date=date.today(),
            contact_no=str(signup.contact_no) if signup.contact_no else ""
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"User signed up successfully: {signup.username}")
        return new_user

    except HTTPException as he:
        logger.error(f"HTTP error during signup: {str(he)}")
        raise he
    except IntegrityError as ie:
        db.rollback()
        logger.error(f"Database integrity error: {str(ie)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database error - possibly duplicate entry"
        )
    except Exception as e:
        logger.error(f"Unexpected error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/login")
async def login(login: Login, db: Session = Depends(get_db)):
    """User login with password hashing check"""
    try:
        # Input validation
        if not login.email or not login.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )

        # Get user by email
        user = db.query(User).filter(User.email == login.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Verify password
        if not pwd_context.verify(login.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        logger.info(f"User logged in successfully: {login.email}")
        return {"message": "Login successful", "user_id": user.id, "username": user.username}

    except HTTPException as he:
        logger.error(f"HTTP error during login: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )