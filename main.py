from fastapi import *
from fastapi.responses import FileResponse
from backend.route import index, login
from fastapi.staticfiles import StaticFiles


app = FastAPI()
app.mount("/static" ,StaticFiles(directory="static"), name="static")
app.include_router(login.router)
app.include_router(index.router)

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

@app.get("/loginButton")
async def login_page():
	file_path = "./static/html/login.html"
	return FileResponse(file_path, media_type="text/html")