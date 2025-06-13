import logging
from fastapi import FastAPI

from auth.models import RegisterModel, LoginModel
from auth.auth import register_user, login_user

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/")
async def root():
    logger.info("GET / - Root endpoint accessed")
    return {"message": "Server is running!"}

@app.post("/register")
async def register(data: RegisterModel):
    logger.info(f"POST /register - Register request for email: {data.email}")
    result = await register_user(data)
    logger.info(f"POST /register - Response: {result}")
    return result

@app.post("/login")
async def login(data: LoginModel):
    logger.info(f"POST /login - Login attempt for email: {data.email}")
    result = await login_user(data)
    logger.info(f"POST /login - Response: {result}")
    return result