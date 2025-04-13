from fastapi import FastAPI
from db import engine
import models
from fastapi.staticfiles import StaticFiles
from routes import router 
from fastapi.middleware.cors import CORSMiddleware  # Import only once

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Add middleware BEFORE mounting any routes or static files
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://bazaarpakistan.up.railway.app",
        "http://bazaarpakistan.up.railway.app",
        "https://www.bazaarpakistan.up.railway.app",
        "http://www.bazaarpakistan.up.railway.app",
        # Include any localhost URLs you might be using for development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Authorization"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Mount static files and include routers AFTER middleware
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.include_router(router)

@app.options("/{rest_of_path:path}")
async def options_route(rest_of_path: str):
    return {"detail": "OK"}

@app.get("/")
def read_root():
    return {"message": "Welcome to the Bazaar app!"}