from fastapi import FastAPI
from app.database.db import engine
from app.database.db import Base
from app.routers import auth_router, recommendation_router, article_router, interaction_router, search_router, trending_router, user_router, analytics_router
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging_config import configure_logging
from app.core.middleware import RequestLoggingMiddleware

configure_logging()
app = FastAPI()

# main.py is the entry point of the application, it creates the FastAPI app and includes all the routers for the different endpoints. It also sets up the database connection and creates the tables if they do not exist. It also sets up the CORS middleware to allow requests from the frontend and also adds a custom middleware to log all the incoming requests for better debugging and monitoring of the application.

# Allowing requests from only two endpoints
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for logging all the incoming requests
app.add_middleware(RequestLoggingMiddleware)
Base.metadata.create_all(bind=engine)


# all the routers of that are to be included in the main server
app.include_router(auth_router.router)
app.include_router(recommendation_router.router)
app.include_router(article_router.router)
app.include_router(interaction_router.router)
app.include_router(search_router.router)
app.include_router(trending_router.router)
app.include_router(user_router.router)
app.include_router(analytics_router.router)