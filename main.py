from fastapi import FastAPI, Response
from db import engine
import models
from fastapi.staticfiles import StaticFiles
from routes import router
from fastapi.middleware.cors import CORSMiddleware

# Create database tables (initialization)
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI()

# Static files handling
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bazaarpakistan.up.railway.app"],  # Allow only this origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bazaarpakistan.up.railway.app"],  # Allow only this origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Bazaar app!"}
