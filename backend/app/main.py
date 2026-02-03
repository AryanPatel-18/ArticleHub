from fastapi import FastAPI
from database.db import engine
from database.db import Base
from routers import auth_router, recommendation_router, article_router, interaction_router, search_router, trending_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allowing requests from all posts
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


app.include_router(auth_router.router)
app.include_router(recommendation_router.router)
app.include_router(article_router.router)
app.include_router(interaction_router.router)
app.include_router(search_router.router)
app.include_router(trending_router.router)