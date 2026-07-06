from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import UserSignupRequest, UserLoginRequest, TokenResponse, UserResponse
from app.utils.auth_helper import hash_password, verify_password, create_access_token, get_current_user
from app.utils.db import db_instance
from app.utils.logger import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=TokenResponse)
async def signup(payload: UserSignupRequest):
    """Registers a new user, hashes password, saves to MongoDB, and returns access token."""
    if db_instance.db is None:
        raise HTTPException(
            status_code=500,
            detail="Database connection is not initialized."
        )
        
    users_collection = db_instance.db["users"]
    
    # Check if email already registered
    existing_email = await users_collection.find_one({"email": payload.email})
    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists."
        )
        
    # Check if username already registered
    existing_username = await users_collection.find_one({"username": payload.username})
    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="This username is already taken."
        )
        
    # Hash password and save user
    hashed_pwd = hash_password(payload.password)
    user_document = {
        "email": payload.email,
        "username": payload.username,
        "password": hashed_pwd
    }
    
    try:
        await users_collection.insert_one(user_document)
        logger.info(f"Registered new user: {payload.username} ({payload.email})")
    except Exception as e:
        logger.error(f"Failed to register user to MongoDB: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to save user account."
        )

    # Create access token and log user in immediately
    access_token = create_access_token(data={"sub": payload.email})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(email=payload.email, username=payload.username)
    )

@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLoginRequest):
    """Authenticates credentials against MongoDB and returns access token."""
    if db_instance.db is None:
        raise HTTPException(
            status_code=500,
            detail="Database connection is not initialized."
        )
        
    users_collection = db_instance.db["users"]
    
    user = await users_collection.find_one({"email": payload.email})
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )
        
    if not verify_password(payload.password, user["password"]):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )
        
    logger.info(f"User logged in successfully: {user['username']}")
    
    access_token = create_access_token(data={"sub": user["email"]})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(email=user["email"], username=user["username"])
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Retrieves current authenticated user's information from current session."""
    return UserResponse(
        email=current_user["email"],
        username=current_user["username"]
    )
