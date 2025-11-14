# For main.py
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from databases import Database
from urllib.parse import quote_plus

DB_USER = "postgres"
DB_PASSWORD = quote_plus("Admin@123")  # encode special chars
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "DB1"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLAlchemy
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Async database object
database = Database(DATABASE_URL)

# Table
Emp = Table(
    "EMP2",
    metadata,
    Column("Id", Integer, primary_key=True),
    Column("Username", String(100)),
    Column("Email", String(50)),
    Column("P_no", String(50)),
    Column("Image",String(200))
)

# Create table
metadata.create_all(engine)

# For Authenication 

from sqlalchemy import create_engine, Column, Integer, String,Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus

user = "postgres"
password = quote_plus("Admin@123")
host = "localhost"
database = "DB1"

SQLALCHEMY_DATABASE_URL = f"postgresql://{user}:{password}@{host}/{database}"

# Create the database engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Session Local to interact with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class to define the database models
Base = declarative_base()

# Database model for users
class User(Base):
    __tablename__ = "auth"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    hashed_password = Column(String)
    disabled = Column(Boolean, default=0)

    # Add username and password manually by insert queries into auth table to test the authorization in postman

# Create the tables in the database (this will create the 'users' table)
def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
