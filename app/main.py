from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
from app.routers import auth, posts

app = FastAPI(title="Clue Mini-Blog")

app.add_middleware(SessionMiddleware, secret_key="super_secret_key_12345_clue")

app.include_router(auth.router)
app.include_router(posts.router)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_index():
    return FileResponse("static/index.html")