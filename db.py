import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import inspect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Retrieve the database URL from environment variables
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Create the engine for SQLAlchemy to connect to the database
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a sessionmaker instance
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test connection when this module is imported
def test_connection():
    try:
        # Create inspector first
        inspector = inspect(engine)
        
        # Import here to avoid circular imports
        from models import User
        
        # Create a session
        db = SessionLocal()
        
        # Try to get a user
        user = db.query(User).first()
        
        if user:
            logger.info(f"✅ Database connection successful! Found user: {user.username}, email: {user.email}")
        else:
            # Check if the users table exists
            if 'user' in inspector.get_table_names():
                logger.info("✅ Database connected successfully but no users found in the table.")
            else:
                logger.info("✅ Database connected but users table doesn't exist yet.")
        
        # Show all available tables
        tables = inspector.get_table_names()
        logger.info(f"Available tables in database: {tables}")
        
        db.close()
        return True
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {str(e)}")
        return False

# Run the test when this module is imported
connection_successful = test_connection()