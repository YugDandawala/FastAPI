from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from database import SessionLocal, User as DBUser 
from sqlalchemy.orm import Session

SECRET_KEY = "83daa0256a2289b0fb23693bf1f6034d44396675749244721a2b20e896e11662"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

    class Config:
        orm_mode = True

class UserInDB(User):
    hashed_password: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

app = FastAPI()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: Session, username: str):
    """Fetch a user from the DB by username."""
    return db.query(DBUser).filter(DBUser.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credential_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credential_exception

    user = get_user(db, token_data.username)
    if user is None:
        raise credential_exception

    return user

async def get_current_active_user(current_user: DBUser = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: DBUser = Depends(get_current_active_user)):
    return current_user

@app.get("/users/{user_id}")
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    return db.query(DBUser).filter(DBUser.id == user_id).first()

@app.get("/users/me/items")
async def read_own_items(current_user: DBUser = Depends(get_current_active_user)):
    return [{"item_id": 1, "owner": current_user.username}]


-- Build an AI endpoint wiht FastAPI and gemini as our llm model
# https://youtu.be/uDUfZyNXFX0?si=_igLCYg2C9dLI8KE

# Authentication by jwt bearer token and tested in postman is working properly 

Step 1:
- In Postman after creating collection.
- create a post request add [ {url}/token ] then go to body select { x-www-form-urlencoded } add key and value [ { key=username,value=Ex(yug) } ,{ key=password,value=Ex(yug1234) } ]
  and send the request it will give a access token like this {"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhYmMiLCJleHAiOjE3NjMwOTU4NTF9.nwyV9oGpvGiFJPuRrI7Uy0j6hrHWbiXJ-Nrn0Y9R3iI"}

Step 2:
- create a get request [ {url}/users/me ] then go to authorization select Bearer Token and add the access token there ,send the request it will provide you the data of user

Step 3:
- create a get request [ {url}/users/me/items ] then go to authorization select Bearer Token and add the access token there ,send the request it will provide you the data of user

Step 4:
- create a get request [ {url}/users/{user_id} ] then go to authorization select Bearer Token and add the access token there ,send the request it will provide you the data of user with given ID

