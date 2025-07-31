from fastapi import *
from fastapi.responses import FileResponse
from backend.route import index, login, public,send,private,details,member,form
from fastapi.staticfiles import StaticFiles


app = FastAPI()
app.mount("/static" ,StaticFiles(directory="static"), name="static")

app.include_router(login.router)
app.include_router(index.router)
app.include_router(public.router)
app.include_router(send.router)
app.include_router(private.router)
app.include_router(details.router)
app.include_router(member.router)
app.include_router(form.router)

@app.get("/",include_in_schema=False)
async def home_page():
	file_path = "./static/html/index.html"
	return FileResponse(file_path, media_type="text/html")

@app.get("/privateAdoption",include_in_schema=False)
async def private_page():
	file_path = "./static/html/privateAdoption.html"
	return FileResponse(file_path, media_type="text/html")

@app.get("/publicAdoption",include_in_schema=False)
async def public_page():
	file_path = "./static/html/publicAdoption.html"
	return FileResponse(file_path, media_type="text/html")

@app.get("/sendAdoption",include_in_schema=False)
async def send_page():
	file_path = "./static/html/sendAdoption.html"
	return FileResponse(file_path, media_type="text/html")

@app.get("/login",include_in_schema=False)
async def login_page():
	file_path = "./static/html/login.html"
	return FileResponse(file_path, media_type="text/html")

@app.get("/details/{id}",include_in_schema=False)
async def Details(request: Request, id: int):
	file_path = "./static/html/Details.html"
	return FileResponse(file_path, media_type="text/html")

@app.get("/member",include_in_schema=False)
async def Details(request: Request):
	file_path = "./static/html/member.html"
	return FileResponse(file_path, media_type="text/html")

@app.get("/question/{post_id}",include_in_schema=False)
async def Details(request: Request):
	file_path = "./static/html/create_question.html"
	return FileResponse(file_path, media_type="text/html")

@app.get("/ans/{post_id}",include_in_schema=False)
async def Details(request: Request):
	file_path = "./static/html/ans.html"
	return FileResponse(file_path, media_type="text/html")

@app.get("/read",include_in_schema=False)
async def read(request: Request):
	file_path = "./static/html/form_read.html"
	return FileResponse(file_path, media_type="text/html")

@app.get("/revise",include_in_schema=False)
async def read(request: Request):
	file_path = "./static/html/form_revise.html"
	return FileResponse(file_path, media_type="text/html")