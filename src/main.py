from fastapi import FastAPI
import logging
import uvicorn

from .api.routes import router
from .core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_TITLE)

# Include API routes
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
