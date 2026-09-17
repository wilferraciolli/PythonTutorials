# Fast API tutorial


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

## Running the app
```bash
uvicorn main:app --reload
```