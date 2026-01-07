from fastapi import FastAPI
from database.db import engine
from database.db import Base
from routers import auth_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allowing requests from all posts
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


app.include_router(auth_router.router)
