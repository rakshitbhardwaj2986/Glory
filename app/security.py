from jose import jwt, JWTError  # type: ignore[import]
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer 
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from .Database import get_db
from .models import User  

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

#  Password Hashing
def hash_password(password: str):
    return pwd_context.hash(password[:72])

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password[:72], hashed_password)

#  JWT Config
SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = timedelta(minutes=60*24)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Create Token
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + ACCESS_TOKEN_EXPIRE_MINUTES
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

#  Get Current User (AUTHENTICATION)
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")

        if email is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()

    if user is None:
        raise credentials_exception

    return user

#  ADMIN AUTHORIZATION
def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return current_user

# EMPLOYER AUTHORIZATION
def require_employer(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["employer", "admin"]:
        raise HTTPException(status_code=403, detail="Employers only")
    return current_user

# JOBSEEKER AUTHORIZATION
def require_jobseeker(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["jobseeker", "admin"]:
        raise HTTPException(status_code=403, detail="Jobseekers only")
    return current_user
