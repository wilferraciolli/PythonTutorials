## **Step 1: Install Python**


### **Recommended Version**



- **Python 3.10 or higher** (3.11+ is ideal)

- FastAPI requires Python 3.7+, but 3.11/3.12 are the sweet spot



### **Installation Options:**


**Option A: Download from python.org**



1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)

2. Download **Python 3.11 or 3.12** (Windows installer)

3. **IMPORTANT:** Check ✅ **"Add Python to PATH"** during installation

4. Click "Install Now"



**Option B: Verify if Python is already installed**

Run in your terminal:


Bash






```
python --version

```






## 🗂️ **Step 2: Create Your Project Structure**


Assuming you have a git folder, let's set it up. Run these commands:


Bash






```
# Navigate to your git folder (replace with your actual path)
cd C:\path\to\your\git\folder

# Create project directory
mkdir fastapi-learning
cd fastapi-learning

# Initialize git (if not already done)
git init

```






## 🔧 **Step 3: Create Virtual Environment**


**Critical:** Always use virtual environments in Python (like separate Maven projects).


Bash






```
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# You should see (venv) at the start of your terminal prompt

```






## 📥 **Step 4: Install FastAPI & Dependencies**


Bash






```
# Upgrade pip first
python -m pip install --upgrade pip

# Install FastAPI and Uvicorn (web server)
pip install fastapi uvicorn[standard]

# Install useful tools
pip install python-dotenv requests

```





**Verify installation:**


Bash






```
pip list

```






## 📝 **Step 5: Create Your First FastAPI Project**


Create these files in your project folder:


### **File 1: `main.py`** (Your REST API)


Python






```
from fastapi import FastAPI

# Create app instance (like Spring Boot Application)
app = FastAPI(title="My First API", version="1.0.0")

# GET endpoint (like @GetMapping in Spring)
@app.get("/")
def read_root():
    return {"message": "Hello, Python!"}

# GET with parameter
@app.get("/hello/{name}")
def hello(name: str):
    return {"message": f"Hello, {name}!"}

# GET with query parameter
@app.get("/users")
def get_users(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

# POST endpoint (like @PostMapping)
@app.post("/users")
def create_user(name: str, email: str):
    return {"id": 1, "name": name, "email": email}

```





### **File 2: `.gitignore`**


Plain text






```
venv/
__pycache__/
*.pyc
*.pyo
.env
.DS_Store
dist/
build/
*.egg-info/

```





### **File 3: `requirements.txt`** (like pom.xml dependencies)


Plain text






```
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0

```





**Generate it automatically:**


Bash






```
pip freeze > requirements.txt

```






## 🚀 **Step 6: Run Your API**


Bash






```
# Make sure venv is activated
uvicorn main:app --reload

# You should see:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete

```






## 🌐 **Step 7: Test Your API**


### **Option 1: Browser**


Open: `http://localhost:8000/hello/Alice`


### **Option 2: Interactive Docs (Swagger UI)**


Go to: `http://localhost:8000/docs`


### **Option 3: curl (like Postman)**


Bash






```
curl http://localhost:8000/hello/Alice
curl -X POST "http://localhost:8000/users?name=Bob&email=bob@example.com"

```






## 📁 **Final Project Structure**


Plain text






```
fastapi-learning/
├── venv/                  # Virtual environment (don't commit)
├── main.py               # Your API code
├── requirements.txt      # Dependencies
├── .gitignore           # Git ignore rules
└── .git/                # Git folder

```






## ⚡ **Quick Cheat Sheet for You (Java → Python)**












































| Java | Python |
| --- | --- |
| `@GetMapping` | `@app.get()` |
| `@PostMapping` | `@app.post()` |
| `@PathVariable` | Path parameter in function |
| `@RequestParam` | Query parameter in function |
| `@RequestBody` | Pydantic model |
| `try/catch` | `try/except` |
| `new ArrayList<>()` | `[]` |
| `new HashMap<>()` | `{}` |




## **Ready? Pick Your Next Step:**



1. ✅ **Follow the commands above** in your terminal (I've opened it for you)

2. 📝 Create the files I showed you

3. 🚀 Run `uvicorn main:app --reload`

4. 🌐 Visit `http://localhost:8000/docs` to see your API docs



**Would you like me to:**



- Walk you through each command live?

- Create these files directly in your project?

- Explain any specific part deeper?



Let me know! 🎯