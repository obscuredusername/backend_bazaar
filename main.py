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

# ✅ CORS middleware should be right after creating app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bazaarpakistan.up.railway.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⬇️ Routes and other stuff come after
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.include_router(router)



@app.get("/")
def read_root():
    return {"message": "Welcome to the Bazaar app!"}
