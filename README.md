# TWS CORE

## API Docs

API documentation is automatically generated using Swagger. You can view documention by visiting at these paths

```bash
swagger/
redoc/
```


## Local Development without Docker

### Install

```bash
# note: this is bash running on windows env/scripts/activate might be env/bin/activate on a full linux environment

git clone [[repo]]

cd [[repo]]

# create virtual environment
python3 -m venv env

# activate virtual environment
source env/scripts/activate

# create configuration file
cp .env.dist .env

# install requirements
pip install -r requirements/dev.txt

python manage.py migrate
python manage.py collectstatic --noinput
```

### Run dev server

This will run server on [http://localhost:8000](http://localhost:8000)

```bash
python manage.py runserver
```

### Create superuser

If you want, you can create initial super-user with next commad:

```bash
python manage.py createsuperuser
```

### Setup database
The default database is sqlite (unsuitable for production), to switch to MySQL, ie. after renaming `.env.example` to `.env`, follow the following steps.

At your .env file
```bash
# Changed to False
USE_DEFAULT_BACKEND=False

# wil use sqlite 
USE_DEFAULT_BACKEND=True

# set to either mysql or postgres
ALT_BACKEND=mysql

# Set these according to your database server
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
```

#### Ensure mysqlclient is installed
```bash
# activate virtual environment first
pip install mysqlclient
```

That should do it.


### With Docker
Docker is setup to work with postgres. to use docker change the following in your `.env` config file.


```bash
# wil use sqlite 
USE_DEFAULT_BACKEND=False

# set to either mysql or postgres
ALT_BACKEND=postgres

# Set these according to your database server
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
```

## Local Development with Docker

Start the dev server for local development:

```bash
cp .env.dist .env
docker-compose up
```

Run a command inside the docker container:

```bash
docker-compose run --rm web [command]
```
