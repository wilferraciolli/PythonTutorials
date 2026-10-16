# Python json processing

To be able to parse json and write json, we need to install the simplejson library with the following command
```bash
pip install simplejson
``` 

## Creating virtual environments
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