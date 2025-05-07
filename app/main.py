from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    return app


app = create_app()