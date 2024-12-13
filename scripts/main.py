from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from scripts.router.api import router

logger = logging.getLogger(__name__)

app = FastAPI()

origins = [
  
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    logger.info("Health check")
    return {"status": "OK"}

app.include_router(router)