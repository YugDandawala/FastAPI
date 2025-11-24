from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus

# ---------- Update these with your Postgres credentials ----------
user = "postgres"
password = quote_plus("Admin@123")   # escape special chars
host = "localhost"
port = "5432"
database = "DB1"
# ----------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"

# ---------- SQLAlchemy Engine ----------
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ---------- User Table ----------
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    parent_id = Column(Integer, nullable=True)   # parent user's user_id
    disabled = Column(Boolean, default=False)

# ---------- Create Tables ----------
def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
