from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from passlib.hash import bcrypt
from pydantic import BaseModel
from tortoise.models import Model
from tortoise.fields import CharField, IntField
from tortoise.contrib.fastapi import register_tortoise

app = FastAPI()

# CORS middleware setup
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],  # or ["GET", "POST"] if you prefer
    allow_headers=["*"],  # or list specific headers
)

register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",  # Replace with Postgres for production
    modules={"models": ["backend.app.main"]},
    generate_schemas=True,
    add_exception_handlers=True,
)


class User(Model):
    id = IntField(primary_key=True)
    username = CharField(max_length=50, unique=True)
    password_hash = CharField(max_length=128)
    role = CharField(max_length=20, default="customer")

    def check_password(self, password: str) -> bool:
        return bcrypt.verify(password, self.password_hash)

    class Meta:
        table = "users"


class LoginData(BaseModel):
    username: str
    password: str


@app.post("/login")
async def login(data: LoginData) -> Dict[str, Any]:
    user = await User.get_or_none(username=data.username)
    if not user or not user.check_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": f"Hello, {user.username}!"}
