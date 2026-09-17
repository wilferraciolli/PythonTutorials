from fastapi import FastAPI

# Create app initializer
app= FastAPI(title = "Tutorial", version = "1.0.0")

# GET
@app.get("/")
def read_root():
  return {"message": f"Hello World"}



