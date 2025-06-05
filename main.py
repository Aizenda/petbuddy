from fastapi import *
from fastapi.responses import FileResponse
from backend.route import index, login, public,send,private,details,member
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

@app.get("/")
async def home_page():
	file_path = "./static/html/index.html"
	return FileResponse(file_path, media_type="text/html")

@app.get("/privateAdoption")
async def private_page():
	file_path = "./static/html/privateAdoption.html"
	return FileResponse(file_path, media_type="text/html")

@app.get("/publicAdoption")
async def public_page():
	file_path = "./static/html/publicAdoption.html"
	return FileResponse(file_path, media_type="text/html")

@app.get("/sendAdoption")
async def send_page():
	file_path = "./static/html/sendAdoption.html"
	return FileResponse(file_path, media_type="text/html")

@app.get("/login")
async def login_page():
	file_path = "./static/html/login.html"
	return FileResponse(file_path, media_type="text/html")

@app.get("/details/{id}")
async def Details(request: Request, id: int):
	file_path = "./static/html/Details.html"
	return FileResponse(file_path, media_type="text/html")

@app.get("/member")
async def Details(request: Request):
	file_path = "./static/html/member.html"
	return FileResponse(file_path, media_type="text/html")