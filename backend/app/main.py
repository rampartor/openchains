# backend/app/main.py
from fastapi import FastAPI, HTTPException, Depends, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, Annotated
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt
from tortoise.models import Model
from tortoise.fields import CharField, IntField, DatetimeField, BooleanField
from tortoise.contrib.fastapi import register_tortoise


# Define token models
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Create the FastAPI app
app = FastAPI(title="OpenChains")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://frontend:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define your User model
class User(Model):
    id = IntField(pk=True)
    username = CharField(max_length=50, unique=True)
    password = CharField(max_length=100)
    is_active = BooleanField(default=True)
    created_at = DatetimeField(auto_now_add=True)

    class Meta:
        table = "users"


# Define input models
class UserCreate(BaseModel):
    username: str
    password: str


# Password utilities
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, "your-secret-key", algorithm="HS256")
    return encoded_jwt


# Login endpoint
@app.post("/login", response_model=Token)
async def login(
        username: Annotated[str, Form()],
        password: Annotated[str, Form()]
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    print(f"Login attempt for username: {username}")

    # Find the user
    user = await User.get_or_none(username=username)

    if not user:
        print(f"User not found: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check password
    if not verify_password(password, user.password):
        print(f"Password verification failed for user: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    print(f"Login successful for user: {username}")

    # Generate token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


# Add OAuth2 compatible endpoint
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await User.get_or_none(username=form_data.username)

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


# Registration endpoint
@app.post("/register")
async def register_user(user: UserCreate):
    # Check if username already exists
    existing_user = await User.get_or_none(username=user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Hash the password
    hashed_password = get_password_hash(user.password)

    # Create new user
    user_obj = await User.create(
        username=user.username,
        password=hashed_password
    )

    return {"message": "User created successfully", "user_id": user_obj.id}


# Create a test user on startup
@app.on_event("startup")
async def create_default_user():
    try:
        # Check if we have any users
        user_count = await User.all().count()
        if user_count == 0:
            print("No users found. Creating default test user...")
            # Create a test user
            hashed_password = get_password_hash("testpassword")
            await User.create(
                username="testuser",
                password=hashed_password,
            )
            print("Default user created: username=testuser, password=testpassword")
    except Exception as e:
        print(f"Error creating default user: {e}")


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
