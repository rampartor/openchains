from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from tortoise import Tortoise, fields, models
from tortoise.contrib.fastapi import register_tortoise
from passlib.hash import bcrypt

app = FastAPI()

# If you're accessing from "http://localhost:5173" (Svelte's default dev server)
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
    add_exception_handlers=True
)


class User(models.Model):
    id = fields.IntField(primary_key=True)
    username = fields.CharField(max_length=50, unique=True)
    password_hash = fields.CharField(max_length=128)
    role = fields.CharField(max_length=20, default="customer")

    def check_password(self, password: str) -> bool:
        return bcrypt.verify(password, self.password_hash)


class LoginData(BaseModel):
    username: str
    password: str


@app.post("/login")
async def login(data: LoginData):
    user = await User.get_or_none(username=data.username)
    if not user or not user.check_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": f"Hello, {user.username}!"}
