from fastapi import FastAPI, Request, Response
from db import engine
import models
from fastapi.staticfiles import StaticFiles
from routes import router 
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Add middleware before anything else
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all origins to test
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add preflight middleware to handle OPTIONS requests explicitly
@app.middleware("http")
async def options_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response
    return await call_next(request)

# Mount static files and include routers after middleware
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Bazaar app!"}