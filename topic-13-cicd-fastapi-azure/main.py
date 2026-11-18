import os
from fastapi import FastAPI

app = FastAPI(title="CI/CD Demo API")

@app.get("/")
def root():
    return {"app": "CI/CD Demo API", "message": "Hello from FastAPI",
            "environment": os.getenv("APP_ENVIRONMENT", "local"),
            "version": os.getenv("APP_VERSION", "dev")}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/greet/{name}")
def greet(name: str):
    return {"greeting": f"Hello, {name}!"}
