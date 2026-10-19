# Creating virtual environments
Virtual environments are good to keep python dependencies contained within an environment so only the necessary depoendencies are installed on an isolated area
to create an virtual env, install and initiate it with `pip`

```bash
pip install virtualenv
```
Then to create a virtual environment, navigate to the folder you want it is and type, PS give it a name for this case it will be called testenv
```bash
virtualenv testenv
```
Finally activate it
```bash
source testenv/bin/activate

```