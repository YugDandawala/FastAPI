from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from database import Base, engine, SessionLocal
from models import User
from datetime import datetime, timedelta

Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# JWT CONFIG
SECRET_KEY = "83daa0256a2289b0fb23693bf1f6034d44396675749244721a2b20e896e11662"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -------------------- DB Session --------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------- HOME PAGE --------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# -------------------- REGISTER --------------------
@app.post("/register")
def register(
    username: str = Form(...),
    password: str = Form(...),
    parentid: int = Form(None),
    db: Session = Depends(get_db)
):
    hashed_password = pwd_context.hash(password)

    # Validate parent ID
    if parentid:
        parent = db.query(User).filter(User.userid == parentid).first()
        if not parent:
            return {"error": "Parent ID does not exist"}

    new_user = User(username=username, password=hashed_password, parentid=parentid, disabled=False)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RedirectResponse(url="/login", status_code=302)


# -------------------- LOGIN PAGE --------------------
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# -------------------- JWT LOGIN ENDPOINT --------------------
@app.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token_data = {"sub": user.username, "user_id": user.userid}
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    token_data.update({"exp": expire})
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    return {"access_token": token, "token_type": "bearer"}


# -------------------- GET CURRENT USER FROM TOKEN --------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    exception = HTTPException(
        status_code=401,
        detail="Could not validate token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        uid = payload.get("user_id")
        if not username or not uid:
            raise exception
    except JWTError:
        raise exception

    user = db.query(User).filter(User.userid == uid).first()
    if not user:
        raise exception

    return user


# -------------------- SCORE CALCULATION --------------------
def calculate_descendant_score(user: User, db: Session):

    def dfs(u: User, level: int):
        score = 0
        children = db.query(User).filter(User.parentid == u.userid).all()

        for child in children:
            if level == 1:
                score += 20
            elif level == 2:
                score += 10
            elif level == 3:
                score += 5
            else:
                score += 2

            score += dfs(child, level + 1)

        return score

    return dfs(user, 1)


# -------------------- SCORE PAGE --------------------
@app.get("/score", response_class=HTMLResponse)
async def score_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    score_value = calculate_descendant_score(current_user, db)

    return templates.TemplateResponse(
        "score.html",
        {
            "request": request,
            "username": current_user.username,
            "userid": current_user.userid,
            "score": score_value
        }
    )
