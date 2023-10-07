from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Calculator API! Use /add, /subtract, /multiply, /divide endpoints for calculations."}

@app.get("/add")
def add_numbers(number1: int, number2: int):
    return {"result": number1 + number2}

@app.get("/subtract")
def subtract_numbers(number1: int, number2: int):
    return {"result": number1 - number2}

@app.get("/multiply")
def multiply_numbers(number1: int, number2: int):
    return {"result": number1 * number2}

@app.get("/divide")
def divide_numbers(number1: float, number2: float):
    if number2 == 0:
        return {"error": "Division by zero is not allowed."}
    return {"result": number1 / number2}

