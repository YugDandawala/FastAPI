from fastapi import FastAPI, Request, Form, HTTPException,File,UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database import Emp, database
from fastapi.staticfiles import StaticFiles
import shutil
import os

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Employee CRUD")
templates = Jinja2Templates(directory="templates")

# Connect and disconnect database automatically
@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    query = Emp.select()
    employees = await database.fetch_all(query)
    return templates.TemplateResponse("index.html", {"request": request, "employees": employees})


@app.post("/add/", response_class=RedirectResponse)
async def add_employee(id: int = Form(...), username: str = Form(...), email: str = Form(...), pno: str = Form(...),image:UploadFile=File(...)):
   file_path = os.path.join(UPLOAD_DIR, f"Employee{id}.jpg")
   with open(file_path,"wb") as buffer:
      shutil.copyfileobj(image.file, buffer)
   
   query = Emp.insert().values(Id=id, Username=username, Email=email, P_no=pno,Image=file_path)
   await database.execute(query)
   return RedirectResponse("/",status_code=302)


app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/delete/{emp_id}", response_class=RedirectResponse)
async def delete_employee(emp_id: int):
   query = Emp.delete().where(Emp.c.Id == emp_id)
   await database.execute(query)
   return RedirectResponse(url="/",status_code=302)

# Update form for particular Id
@app.get("/edit/{emp_id}", response_class=HTMLResponse)
async def edit_form(request: Request, emp_id: int):
   query = Emp.select().where(Emp.c.Id == emp_id)
   emp = await database.fetch_one(query)
   if not emp:
      raise HTTPException(status_code=404, detail="Employee not found")
   return templates.TemplateResponse("update.html", {"request": request, "emp": emp})

@app.post("/update/{emp_id}", response_class=RedirectResponse)
async def update_employee(emp_id: int, username: str = Form(...), email: str = Form(...), pno: str = Form(...),image:UploadFile=File(...)):
   file_path = os.path.join(UPLOAD_DIR, f"Employee{id}.jpg")
   with open(file_path,"wb") as buffer:
      shutil.copyfileobj(image.file, buffer)

   query = Emp.update().where(Emp.c.Id == emp_id).values(Username=username, Email=email, P_no=pno,Image=file_path)
   await database.execute(query)
   return RedirectResponse(url="/",status_code=302)


# from fastapi import FastAPI, Request, File, UploadFile
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
# import shutil
# import os

# app = FastAPI()
# templates = Jinja2Templates(directory="templates")

# UPLOAD_DIR = "uploads"
# os.makedirs(UPLOAD_DIR, exist_ok=True)  # ensure uploads folder exists


# @app.get("/upload/", response_class=HTMLResponse)
# async def upload(request: Request):
#     return templates.TemplateResponse("file.html", {"request": request})


# @app.post("/uploader/")
# async def upload_files(files: list[UploadFile] = File(...)):
#     uploaded_files = []

#     for file in files:
#         file_path = os.path.join(UPLOAD_DIR, file.filename)
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)
#         uploaded_files.append(file.filename)

#     return {"uploaded_files": uploaded_files}

#Cookie

# from fastapi import FastAPI,Cookie,Response
# from fastapi.responses import JSONResponse

# app=FastAPI()

# @app.get("/cookie/")
# def create_Cookie():
#    content={"message":"cookie set"}
#    response=JSONResponse(content=content)
#    response.set_cookie(key="username",value='admin',max_age=2000,httponly=True,secure=False,samesite="lax")
#    return response

# @app.get("/getCookie/")
# async def read_cookie(username:str|None=Cookie(default=None)):
#    if username:
#       return {"message":f"Hello {username}"}
#    return {"message":"No Cookie found"} 

# @app.get("/delete/")
# def delete_Cookie(response:Response):
#    response.delete_cookie(key="username")
#    return {"message":"Cookie Deleted"}

#Headers

# from typing import Optional
# from fastapi import FastAPI, Header
# app = FastAPI()
# @app.get("/headers/")
# async def read_header(accept_language: Optional[str] = Header(None)):
#    return {"Accept-Language": accept_language} 

# from fastapi.responses import JSONResponse
# @app.get("/rspheader/")
# def set_rsp_headers():
#    content = {"message": "Hello World"}
#    headers = {"X-Web-Framework": "FastAPI", "Content-Language": "en-US"}
#    return JSONResponse(content=content, headers=headers)

#Response Model

# from fastapi import FastAPI
# from typing import List
# from pydantic import BaseModel,Field

# app=FastAPI()

# class student(BaseModel):
#    id:int
#    name:str=Field(None,title="name of Student",max_length=10)
#    marks:List[int]=[]
#    percent_mark:float

# class percent(BaseModel):
#    id:int
#    name:str=Field(None,title="name of Student",max_length=10)
#    percent_mark:float

# @app.post("/marks/",response_model=percent)
# def percent_mark(s1:student):
#    s1.percent_mark=sum(s1.marks)/2
#    return s1
# class supplier(BaseModel):
#    supplierId:int
#    supplierNm:str
# class product(BaseModel):
#    productId:int
#    productNm:str
#    price:int
#    supp:supplier
# class customer(BaseModel):
#    customerId:int
#    customerNm:str
#    prod:List[product]

# @app.post("/invoice")
# def get_invoice(c1:customer):
#    return c1


# class dependency:
#    def __init__(self, id: str, name: str, age: int):
#       self.id = id
#       self.name = name
#       self.age = age 


# async def validate(dep:dependency=Depends()):
#    if dep.age<18:
#       raise HTTPException(status_code=400,detail="You are not eligible")

# @app.get("/user/",dependencies=[Depends(validate)])
# def user():
#    return {"message":"You are eligible"}

# from fastapi.middleware.cors import CORSMiddleware

# origins = [
#    "http://192.168.211.:8000",
#    "http://localhost",
#    "http://localhost:8080",
# ]

# app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

# @app.get("/")
# async def main():
#     return {"message":"hello world "}

# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel

# app = FastAPI()
# data = []

# class Book(BaseModel):
#     id: int
#     title: str
#     author: str
#     publisher: str

# @app.post("/book/")
# def add_book(book: Book):
#     data.append(book.dict())
#     return {"message": "Book added successfully"}

# @app.get("/list/{id}")
# def get_books(id: int):
#     # Find the book with matching id
#     for book in data:
#         if book["id"] == id:
#             return book
#     # If not found, raise 404
#     raise HTTPException(status_code=404, detail="Book not found")
