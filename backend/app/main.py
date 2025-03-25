import random
import time
import typing
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any, AsyncGenerator, Callable, Dict, Optional, Union

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise
from tortoise.fields import BooleanField, CharField, DatetimeField, DecimalField, IntField
from tortoise.models import Model

from backend.app.db_config import TORTOISE_ORM
from backend.tests.config import init_db, setup_prod_app


# Define token models
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Define login request model
class LoginRequest(BaseModel):
    username: str
    password: str


# Define your User model with a role field
class User(Model):
    id = IntField(primary_key=True)
    username = CharField(max_length=50, unique=True)
    password = CharField(max_length=100)
    role = CharField(max_length=20, default="customer")  # Role can be "admin" or "customer"
    is_active = BooleanField(default=True)
    card_number = CharField(max_length=16, null=True)
    created_at = DatetimeField(auto_now_add=True)

    class Meta:
        table = "users"


# Define Slip model
class Slip(Model):
    id = IntField(primary_key=True)
    card_number = CharField(max_length=16)
    amount = DecimalField(max_digits=10, decimal_places=2)
    created_at = DatetimeField(auto_now_add=True)
    updated_at = DatetimeField(auto_now=True)

    class Meta:
        table = "slips"


# Define input models
class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "customer"
    card_number: Optional[str] = None


class SlipCreate(BaseModel):
    card_number: str
    amount: float


class GeneratorRequest(BaseModel):
    user_count: int
    slip_count: int


class GeneratorResponse(BaseModel):
    users_created: int
    slips_created: int
    message: str


# Timing middleware
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], typing.Awaitable[Response]],
    ) -> Response:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Format the time to be more readable (in milliseconds with 2 decimal places)
        formatted_process_time = f"{process_time * 1000:.2f}ms"

        # Add the timing header to the response
        response.headers["X-Process-Time"] = formatted_process_time

        # Log the request with timing information
        path = request.url.path
        method = request.method
        status_code = response.status_code
        print(f"Request: {method} {path} - Status: {status_code} - Time: {formatted_process_time}")

        return response


# Password utilities
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Union[str, datetime]], expires_delta: Optional[timedelta] = None) -> str:
    to_encode: Dict[str, Union[str, datetime]] = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(to_encode, "your-secret-key", algorithm="HS256")
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    user = await User.get_or_none(username=username)
    if user is None:
        raise credentials_exception

    return user  # type: ignore


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    # Initialize the database and perform migrations
    await init_db()
    yield
    # Shutdown logic (if any) would go here
    await Tortoise.close_connections()


app = FastAPI(title="OpenChains", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TimingMiddleware)
setup_prod_app(app)


# OAuth2 token endpoint (unified authentication endpoint)
@app.post("/token", response_model=Token)
async def login_for_access_token(request: LoginRequest) -> Dict[str, str]:
    user = await User.get_or_none(username=request.username)

    if not user:
        print(f"User not found: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(request.password, user.password):
        print(f"Password verification failed for user: {request.username}")
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
    user_obj = await User.create(username=user.username, password=hashed_password, role=user.role)

    return {"message": "User created successfully", "user_id": user_obj.id}


# Endpoint to get current user info
@app.get("/me")
async def get_me(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    return {
        "username": current_user.username,
        "role": current_user.role,
        "is_admin": current_user.role == "admin",
    }


# Generator endpoint for creating random users and slips (admin only)
@app.post("/generator", response_model=GeneratorResponse)
async def generate_data(request: GeneratorRequest, admin: User = Depends(get_admin_user)) -> Dict[str, Union[int, str]]:
    # Validate input
    if request.user_count <= 0 or request.slip_count <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User and slip counts must be positive integers",
        )

    if request.user_count > 1000 or request.slip_count > 5000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum allowed: 1000 users and 5000 slips",
        )

    # Generate and create random users
    users_created = 0
    card_numbers = []

    for i in range(request.user_count):
        username = f"user_{random.randint(10000, 99999)}"
        password = f"pass_{random.randint(10000, 99999)}"
        card_number = "".join([str(random.randint(0, 9)) for _ in range(16)])

        # Check if username already exists
        existing_user = await User.get_or_none(username=username)
        if existing_user:
            continue

        # Hash the password
        hashed_password = get_password_hash(password)

        # Create user
        await User.create(
            username=username,
            password=hashed_password,
            role="customer",
            card_number=card_number,
        )

        card_numbers.append(card_number)
        users_created += 1

    # Generate and create random slips
    slips_created = 0

    for _ in range(request.slip_count):
        if not card_numbers:  # If no users were created, use random card numbers
            card_number = "".join([str(random.randint(0, 9)) for _ in range(16)])
        else:
            card_number = random.choice(card_numbers)

        amount = round(random.uniform(10.0, 1000.0), 2)

        # Create slip
        await Slip.create(card_number=card_number, amount=amount)

        slips_created += 1

    return {
        "users_created": users_created,
        "slips_created": slips_created,
        "message": f"Successfully created {users_created} users and {slips_created} slips",
    }


# Create admin user endpoint (for development)
@app.post("/create-admin")
async def create_admin(admin: UserCreate) -> Dict[str, Union[str, int]]:
    # Check if username already exists
    existing_user = await User.get_or_none(username=admin.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Set role to admin
    admin.role = "admin"

    # Hash the password
    hashed_password = get_password_hash(admin.password)

    # Create admin user
    user_obj = await User.create(username=admin.username, password=hashed_password, role=admin.role)

    return {"message": "Admin user created successfully", "user_id": user_obj.id}


# Register Tortoise ORM
register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=False,  # Don't generate schemas - use Aerich
    add_exception_handlers=True,
)

# For running directly with uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
