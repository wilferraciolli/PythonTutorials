# Fast API tutorial

## Running the app
```bash
uvicorn main:app --reload
```

## Setting up the app
For every python project, you want to create a virtual environment, this is where the program will run
```Bash
# Create virtual environment
python -m venv venv

# Activate it (Windows, if Unix use forward slash)
source venv/Scripts/activate

# You should see (venv) at the start of your terminal prompt
```

After then you need to upgrade the pip
```bash
# Now upgrade pip
python -m pip install --upgrade pip

# Install FastAPI and Uvicorn
pip install fastapi uvicorn[standard]

# Install useful tools
pip install python-dotenv requests
```

Finally verify that all the dependencies were installed
```bash
pip list
```

### Dependencies
Create the dependencies file Eg like pom.xml
```bash
pip freeze > requirements.txt
```

Install dependencies
```bash
pip install -r requirements.txt
```




## 📚 Understanding: FastAPI Routers (Like Java Controllers)


### **Java Comparison**


Java






```
// Java - Separate Controller
@RestController
@RequestMapping("/health")
public class HealthController {
    @GetMapping
    public Map<String, String> healthCheck() {
        return Map.of("status", "API is running");
    }
}

```





### **FastAPI Equivalent**


Python






```
# Python - Separate Router
from fastapi import APIRouter

router = APIRouter(prefix="/health")

@router.get("/")
def health_check():
    return {"status": "API is running"}

```





### **Then in main.py, you register it:**


Python






```
from routers import health

app.include_router(health.router)

```






## 🏗️ What You Need to Do


### **Step 1: Create Folder Structure**


Plain text






```
fastapi-learning/
├── routers/           # NEW FOLDER
│   ├── __init__.py   # Empty file (makes it a package)
│   ├── health.py     # NEW - Health endpoints
│   └── todos.py      # NEW - TODO endpoints
├── main.py           # Keep, but simplified
├── models.py         # Keep as is
└── venv/

```





### **Step 2: Create `routers/__init__.py`**



- Just an empty file (tells Python this is a package)



### **Step 3: Create `routers/health.py`**



- Cut the health endpoint from `main.py`

- Paste into `routers/health.py`

- Wrap it with `APIRouter`



### **Step 4: Create `routers/todos.py`**



- Cut all TODO endpoints from `main.py`

- Paste into `routers/todos.py`

- Wrap it with `APIRouter`



### **Step 5: Update `main.py`**



- Remove all endpoints

- Import the routers

- Register them with `app.include_router()`



### **Step 6: Test**



- Run `uvicorn main:app --reload`

- Check `/docs` still works

- All endpoints still work




## 💡 Key Insight


Think of it like this:



- **Before:** One giant `main.py` with everything mixed together

- **After:** Organized modules, each handling one concern (health, todos)



Same functionality, **much cleaner code!**