# backend/app/main.py
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, AsyncGenerator, Dict, Optional, Union

from fastapi import Depends, FastAPI, Form, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise
from tortoise.fields import BooleanField, CharField, DatetimeField, IntField
from tortoise.models import Model

from backend.tests.config import init_db, setup_prod_app


# Define token models
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Define your User model with a role field
class User(Model):
    id = IntField(primary_key=True)
    username = CharField(max_length=50, unique=True)
    password = CharField(max_length=100)
    role = CharField(
        max_length=20, default="customer"
    )  # Role can be "admin" or "customer"
    is_active = BooleanField(default=True)
    created_at = DatetimeField(auto_now_add=True)

    class Meta:
        table = "users"


# Define input models
class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "customer"


# Password utilities
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Union[str, datetime]], expires_delta: Optional[timedelta] = None
) -> str:
    to_encode: Dict[str, Union[str, datetime]] = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(to_encode, "your-secret-key", algorithm="HS256")
    return encoded_jwt


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    # Initialize the database and perform migrations
    await init_db()
    yield
    # Shutdown logic (if any) would go here
    await Tortoise.close_connections()


app = FastAPI(title="OpenChains", lifespan=lifespan)

setup_prod_app(app)


# Login endpoint
@app.post("/login", response_model=Token)
async def login(
    username: Annotated[str, Form()], password: Annotated[str, Form()]
) -> Dict[str, str]:
    user = await User.get_or_none(username=username)

    if not user:
        print(f"User not found: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(password, user.password):
        print(f"Password verification failed for user: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": username, "role": user.role}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


# Add OAuth2 compatible endpoint
@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Dict[str, str]:
    user = await User.get_or_none(username=form_data.username)

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}


# Registration endpoint
@app.post("/register")
async def register_user(user: UserCreate) -> Dict[str, Union[str, int]]:
    # Check if username already exists
    existing_user = await User.get_or_none(username=user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Hash the password
    hashed_password = get_password_hash(user.password)

    # Create new user
    user_obj = await User.create(
        username=user.username, password=hashed_password, role=user.role
    )

    return {"message": "User created successfully", "user_id": user_obj.id}


# Register Tortoise ORM
register_tortoise(
    app,
    db_url="postgres://postgres:postgres@postgres:5432/openchains",
    modules={"models": ["backend.app.main"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

# For running directly with uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
