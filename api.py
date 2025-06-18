from fastapi import FastAPI
import logging

from main_router import router as auth_router
from quis_router import router as quiz_router

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/")
async def root():
    logger.info("GET / - Root endpoint accessed")
    return {"message": "Server is running!"}


# Include routers
app.include_router(auth_router)
app.include_router(quiz_router)
