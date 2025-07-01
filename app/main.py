
from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel
from typing import Optional
from app.calculator import Calculator

app = FastAPI()

class CalculationRequest(BaseModel):
    """Model for calculation requests"""
    a: float
    b: float

class PowerRequest(BaseModel):
    """Model for power calculation requests"""
    base: float
    exponent: float

class SquareRootRequest(BaseModel):
    """Model for square root calculation requests"""
    number: float

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to Calculator API"}

# Basic arithmetic operations
@app.get("/add")
def add(a: float, b: float):
    """Add two numbers"""
    return {"result": Calculator.add(a, b)}

@app.get("/subtract")
def subtract(a: float, b: float):
    """Subtract second number from first"""
    return {"result": Calculator.subtract(a, b)}

@app.get("/multiply")
def multiply(a: float, b: float):
    """Multiply two numbers"""
    return {"result": Calculator.multiply(a, b)}

@app.get("/divide")
def divide(a: float, b: float):
    """Divide first number by second"""
    try:
        return {"result": Calculator.divide(a, b)}
    except ZeroDivisionError:
        raise HTTPException(status_code=400, detail="Cannot divide by zero")

# Power and square root operations
@app.post("/power")
def power(request: PowerRequest):
    """Calculate power of a number"""
    return {"result": Calculator.power(request.base, request.exponent)}

@app.post("/sqrt")
def sqrt(request: SquareRootRequest):
    """Calculate square root of a number"""
    try:
        return {"result": Calculator.sqrt(request.number)}
    except ValueError:
        raise HTTPException(status_code=400, detail="Cannot calculate square root of negative number")

# Combined operations
@app.post("/calculate")
def calculate(request: CalculationRequest, operation: str = Query(...,
    title="Operation type",
    description="Type of operation to perform (add, subtract, multiply, divide, power, sqrt)",
    pattern="^(add|subtract|multiply|divide|power|sqrt)$"
)):
    """Perform various calculations based on operation type"""
    
    if operation == "add":
        return {"result": Calculator.add(request.a, request.b)}
    elif operation == "subtract":
        return {"result": Calculator.subtract(request.a, request.b)}
    elif operation == "multiply":
        return {"result": Calculator.multiply(request.a, request.b)}
    elif operation == "divide":
        try:
            return {"result": Calculator.divide(request.a, request.b)}
        except ZeroDivisionError:
            raise HTTPException(status_code=400, detail="Cannot divide by zero")
    elif operation == "power":
        return {"result": Calculator.power(request.a, request.b)}
    elif operation == "sqrt":
        try:
            return {"result": Calculator.sqrt(request.a)}
        except ValueError:
            raise HTTPException(status_code=400, detail="Cannot calculate square root of negative number")
