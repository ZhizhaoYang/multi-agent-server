from fastapi import FastAPI, APIRouter, HTTPException
# from .web_base.config.settings import Settings
from app.web_base.routes.chatbot.chat import router as chat_router

from app.web_base.config.settings import Settings

router = APIRouter()


def create_app():
    # app = FastAPI()
    app = FastAPI(
        title="AI Chatbot API",
        version=Settings().VERSION,
    )

    app.include_router(chat_router)

    return app


app = create_app()