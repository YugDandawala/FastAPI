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
