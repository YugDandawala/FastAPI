from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import Union, Annotated
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, init_db, User

# Initialize FastAPI app
app = FastAPI(title="FastAPI with JWT auth Demo")

# OAuth2PasswordBearer is a dependency that provides the token in the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Secret key to encode and decode JWT
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# Create the database tables
init_db()

# Create a Pydantic model for the Token
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Create a Pydantic model for the user data
class TokenData(BaseModel):
    username: Union[str, None] = None

class User(BaseModel):
    username: str
    full_name: Union[str, None] = None
    email: Union[str, None] = None

class UserInDB(User):
    hashed_password: str

# Utility functions to interact with the database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to hash the password
def get_password_hash(password):
    return pwd_context.hash(password)

# Function to verify the password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Function to get a user from the database by username
def get_user(db: Session, username: str) -> Union[UserInDB, None]:
    return db.query(User).filter(User.username == username).first()

# Function to authenticate the user
def authenticate_user(db: Session, username: str, password: str) -> Union[UserInDB, bool]:
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# Function to create a JWT token for a user
def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=15)):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Get current user from the token
def get_current_user(db: Session, token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return User(username=user.username, full_name=user.full_name, email=user.email)

# Get current active user
def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user

@app.post("/token", response_model=Token, tags=['Authentication'])
async def login_for_access_token(db: Session, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/", tags=['public'])
async def read_root():
    return {"message": "Authentication"}

@app.get("/users/me/", response_model=User, tags=['users'])
async def read_user_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user

@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]
