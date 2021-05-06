# Website for COVID-19 testing
![build-test-workflow](https://github.com/anders-biostat/covid-test-web-site/workflows/build-test-workflow/badge.svg?branch=master)

This application is used for COVID-19 tests. Test subjects
can register their test sample and receive the results of the
sample.

![](/doc/media/screenshot.png)

### Build with
- [Django](https://github.com/django/django) (Webapplication Framework)
- [django-rest-framework](https://github.com/encode/django-rest-framework) (REST Framework)
- [Gunicorn](https://github.com/benoitc/gunicorn) (Python WSGI HTTP Server)
- [Semantic UI](https://github.com/Semantic-Org/Semantic-UI) (UI Framework)
- [PostgreSQL](https://github.com/postgres/postgres) (Database)

## Documentation

- [API](/doc/api)
- [Status](/doc/status/README.md)
- [Translation](/doc/translation/README.md)
- [Virtual Environment](/doc/virtualenv/README.md)

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the prerequisites from the 
`src/requirements.txt` file. Using Virtualenv is recommended. See [Virtual Environment](/doc/virtualenv/README.md).

```bash
$ pip install -r requirements.txt
```

Create a `.env` file containing the environment variables in 
the root directory. You can copy the `example.env` 
(make sure you update the secret key):

```bash
$ cp example.env .env
```

### User Permissions
In order for permissions to work, add following groups 
at the admin dashboard. (A superuser does not need to be part of a 
group as he/she is allowed to do everything)
1. Group - name = "lab_user" (User can do everythin within lab interface)
1. Group - name = "bag_handler" (User can only control the bag handout)


## Usage

For testing the application can be started with the command `python manage.py runserver`:
```bash
$ cd covidtest
$ python manage.py runserver
System check identified no issues (0 silenced).
November 02, 2020 - 00:01:23
Django version 3.1.2, using settings 'covidtest.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

For deployment use a appropiate webserver (e.g. Gunicorn).

## Docker

This application can be started in Docker-Containers.
A setup with Docker, Gunicorn, Nginx and Postgres can be composed with the docker-compose.yml configuration.

```bash
$ sudo docker-compose up
Starting backend_postgres ... done
Starting covidtest_app    ... done
Starting covidtest_nginx  ... done
Attaching to covidtest_postgres, covidtest_app, covidtest_nginx
```