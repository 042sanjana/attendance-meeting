from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.org_routes import router
from database.db import create_tables

app = FastAPI()

create_tables()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
         "http://localhost:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)