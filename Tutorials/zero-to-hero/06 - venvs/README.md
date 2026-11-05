# Virtual environments and module management

Virtual environments are way to install python and its dependencies within a folder, so the project will run based on that environment so you can have multiple virtual
environments with different versions.
this is also ideal to make sure that prod and dev will also work as expected.


### Creating a virtual environment using `uv`
The UV is the best venv and package manager for Python (replacement for pip), this needs to be installed separetely.

Type is the command below to instantiate a virtual environment, create the pyproject.toml dependencies files and the uv.lock file this will create the `.venv` folder which will create the python interpreter and handle all of the dependencies

```bash
    uv init my-project
```

To query which version of python it is running type in `which python`, it should print the python interpreter that the venv is using


# Declaring dependencies
Use the command below to add dependencies
```bash 
    uv add fastapi
```
To install dependencies (Eg another machine) run 
```bash
    uv sync
```

# Running the app simply type in
```bash
    uv run python main.py
```





































