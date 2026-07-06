import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from fastapi import Header, HTTPException
from app.config import settings
from app.utils.db import db_instance

def hash_password(password: str) -> str:
    """Hashes a password string using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password string against a bcrypt hashed password."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Generates a JSON Web Token containing payload claims and expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=2)  # default to 2 hours
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """Decodes a JWT and verifies signature/expiration. Returns claims dict or None."""
    try:
        decoded_token = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return decoded_token
    except jwt.PyJWTError:
        return None

async def get_current_user(authorization: str = Header(None)):
    """FastAPI Dependency checking the authorization header and fetching the user from MongoDB."""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authentication token is missing. Please log in first."
        )
    
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization token format. Use 'Bearer <token>'."
        )
    
    token = parts[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=401,
            detail="Session has expired or is invalid. Please log in again."
        )
    
    email = payload["sub"]
    if db_instance.db is None:
        raise HTTPException(
            status_code=500,
            detail="Database connection is not initialized."
        )
        
    user = await db_instance.db["users"].find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authorized user account could not be found."
        )
        
    return user
