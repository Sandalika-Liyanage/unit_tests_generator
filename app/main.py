
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/add")
def add(a: int, b: int):
    return {"result": a + b}

@app.post("/echo")
def echo(data: dict):
    return {"you_sent": data}
