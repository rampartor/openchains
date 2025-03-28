# Import required modules
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
    role: Optional[str] = "customer"


class AdminCreate(BaseModel):
    username: str
    password: str


# Define middleware for timing requests
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], typing.Awaitable[Response]]) -> Response:
        # Record the start time
        start_time = time.time()

        # Process the request
        response = await call_next(request)

        # Calculate the processing time
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
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate token
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=120),  # 2 hours
    )

    return {"access_token": access_token, "token_type": "bearer"}


# Get your own details
@app.get("/users/me", response_model=Dict[str, Any])
async def read_users_me(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    return {
        "username": current_user.username,
        "role": current_user.role,
        "is_active": current_user.is_active,
    }


# Register endpoint (only for customers by default)
@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate) -> Dict[str, str]:
    # Check if username already exists
    existing_user = await User.get_or_none(username=user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Hash the password
    hashed_password = get_password_hash(user.password)

    # Create user with "customer" role by default
    user_obj = await User.create(username=user.username, password=hashed_password, role=user.role)

    return {"message": "User registered successfully", "user_id": user_obj.id}


# Create admin user (for testing/initialization only)
@app.post("/create-admin", status_code=status.HTTP_201_CREATED)
async def create_admin(admin: AdminCreate) -> Dict[str, Any]:
    # Check if admin already exists
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


@app.get("/generator/stats")
async def get_generator_stats(admin: User = Depends(get_admin_user)) -> Dict[str, int]:
    """Returns statistics about generated test data including user and slip counts."""
    user_count = await User.all().count()
    slip_count = await Slip.all().count()

    return {"user_count": user_count, "slip_count": slip_count}


class GenerateUsersRequest(BaseModel):
    user_count: int


@app.post("/generator/users")
async def generate_users(request: GenerateUsersRequest, admin: User = Depends(get_admin_user)) -> Dict[str, Any]:
    """Generate test users for the system."""
    # Validate input
    if request.user_count <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_count must be greater than 0",
        )

    if request.user_count > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_count must be less than or equal to 1000",
        )

    # Generate users
    created_users = []
    for i in range(request.user_count):
        username = f"test_user_{int(time.time())}_{i}"
        hashed_password = get_password_hash("password123")

        # Create user with randomly generated card number
        card_number = "".join([str(random.randint(0, 9)) for _ in range(16)])
        user = await User.create(username=username, password=hashed_password, role="customer", card_number=card_number)
        created_users.append(user)

    return {
        "message": f"Successfully created {len(created_users)} test users",
        "users_created": len(created_users),
        "users": [
            {"id": user.id, "username": user.username, "card_number": user.card_number} for user in created_users
        ],
    }


class GenerateSlipsRequest(BaseModel):
    min_amount: float = 10.0
    max_amount: float = 5000.0
    bonus_percentage: float = 5.0
    slips_per_user: int = 1


@app.post("/generator/slips")
async def generate_slips(request: GenerateSlipsRequest, admin: User = Depends(get_admin_user)) -> Dict[str, Any]:
    """Generate slips for existing users."""
    # Validate input
    if request.min_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_amount must be greater than 0",
        )

    if request.max_amount <= request.min_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_amount must be greater than min_amount",
        )

    if request.slips_per_user <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="slips_per_user must be greater than 0",
        )

    # Get all users
    users = await User.all()
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found in the system",
        )

    # Generate slips for each user
    slips_created = 0
    for user in users:
        if not user.card_number:
            continue  # Skip users without card numbers

        for _ in range(request.slips_per_user):
            # Generate random amount between min and max
            amount = random.uniform(request.min_amount, request.max_amount)
            amount = round(amount, 2)  # Round to 2 decimal places

            # Create slip
            await Slip.create(card_number=user.card_number, amount=amount)
            slips_created += 1

    return {
        "message": f"Successfully created {slips_created} slips",
        "slips_created": slips_created,
        "users_count": len(users),
    }


@app.post("/generator/rotate")
async def rotate_users(admin: User = Depends(get_admin_user)) -> Dict[str, Any]:
    """Simulate chain rotation by randomly reassigning users in the system."""
    # Get all users
    users = await User.all()
    if not users or len(users) < 6:  # Need at least 6 users to perform rotation
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough users to perform rotation. Need at least 6 users.",
        )

    # For now, simulate rotation - can be expanded with actual chain logic
    rotated_users = random.sample(list(users), min(len(users) // 3, 10))

    return {
        "message": f"Rotation completed for {len(rotated_users)} users",
        "rotated_users": len(rotated_users),
        "users": [{"id": user.id, "username": user.username} for user in rotated_users],
    }


@app.post("/generator/cleanup")
async def cleanup_test_data(admin: User = Depends(get_admin_user)) -> Dict[str, int]:
    """Remove all test users and slips from the database, preserving only admin users."""
    # Get all non-admin users (consider all regular users as test users)
    # We exclude the current admin user to ensure we don't delete ourselves
    non_admin_users = await User.filter(role="customer")
    user_ids = [user.id for user in non_admin_users]

    # Delete all slips - since all slips are test data
    slips_removed = await Slip.all().delete()

    # Delete all non-admin users
    users_removed = 0
    if user_ids:
        users_removed = await User.filter(id__in=user_ids).delete()

    return {"users_removed": users_removed, "slips_removed": slips_removed}


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
