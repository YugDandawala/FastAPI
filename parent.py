from fastapi import Depends, FastAPI, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing import Optional, List
from database import SessionLocal, User as DBUser  # database.py provided above

# ----------------- JWT / Auth config -----------------
SECRET_KEY = "83daa0256a2289b0fb23693bf1f6034d44396675749244721a2b20e896e11662"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

app = FastAPI()
templates = Jinja2Templates(directory="templates")


# ----------------- Pydantic models (for responses) -----------------
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserOut(BaseModel):
    username: str
    disabled: Optional[bool] = None

    class Config:
        orm_mode = True


# ----------------- DB dependency -----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ----------------- password helpers -----------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ----------------- user helpers -----------------
def get_user_by_username(db: Session, username: str):
    return db.query(DBUser).filter(DBUser.username == username).first()


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ----------------- web pages -----------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# ----------------- register endpoint -----------------
@app.post("/register")
def register(
    username: str = Form(...),
    password: str = Form(...),
    parent_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    # Check uniqueness
    if db.query(DBUser).filter(DBUser.username == username).first():
        return {"error": "username already exists"}

    # validate parent if provided
    if parent_id is not None:
        parent = db.query(DBUser).filter(DBUser.user_id == parent_id).first()
        if not parent:
            return {"error": "Parent ID does not exist"}

    hashed = get_password_hash(password)
    new_user = DBUser(username=username, hashed_password=hashed, parent_id=parent_id, disabled=False)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # after registration go to login page
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


# ----------------- token endpoint (login using OAuth2 form) -----------------
@app.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})

    access_token = create_access_token(data={"sub": user.username, "user_id": user.user_id})
    return {"access_token": access_token, "token_type": "bearer"}


# ----------------- get current user from token -----------------
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    cred_exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                             detail="Could not validate credentials",
                             headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        uid = payload.get("user_id")
        if username is None or uid is None:
            raise cred_exc
    except JWTError:
        raise cred_exc

    user = db.query(DBUser).filter(DBUser.user_id == uid).first()
    if user is None:
        raise cred_exc
    return user


async def get_current_active_user(current_user: DBUser = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# ----------------- score based on parent chain (same style you wanted) -----------------
def calculate_score(userid: int, db: Session):
    level = 0
    current = userid

    while True:
        user = db.query(DBUser).filter(DBUser.user_id == current).first()
        # if no user found or parent is None -> reached root (no more parents)
        if not user or user.parent_id is None:
            break
        level += 1
        current = user.parent_id

    # return score based on level
    if level == 0:
        return 0
    elif level == 1:
        return 20
    elif level == 2:
        return 10
    elif level == 3:
        return 5
    else:
        return 2


# ----------------- score page (requires token) -----------------
@app.get("/score", response_class=HTMLResponse)
async def score_page(request: Request, current_user: DBUser = Depends(get_current_active_user),
                     db: Session = Depends(get_db)):
    score_value = calculate_score(current_user.user_id, db)
    return templates.TemplateResponse("score.html", {"request": request, "username": current_user.username,
                                                     "userid": current_user.user_id, "score": score_value})


# ----------------- simple API endpoints to check auth (keeps original behavior) -----------------
@app.get("/users/me")
async def read_users_me(current_user: DBUser = Depends(get_current_active_user)):
    return {"user_id": current_user.user_id, "username": current_user.username, "disabled": current_user.disabled}
