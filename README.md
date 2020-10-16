# Website for COVID-19 testing

This application is used for COVID-19 tests. Test subjects
can register their test sample and receive the results of the
sample.

## Directory structure

- **static**: contains all static assets and templates
- **src**: contains the web application and helping scripts
- **data**: contains key for encryption and test data
- **etc**: config files to be put elsewhere in production

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the prerequisites from the 
`src/requirements.txt` file. Using Virtualenv is recommended.

```bash
$ cd src
$ pip install -r requirements.txt
```

Create a `.env` file containing the environment variables in 
the `src` directory. You can copy the `example.env` 
(make sure you update the secret key):

```bash
$ cd src
$ cp example.env .env
```

## Usage

For testing the application can be started with the command `flask run`:
```bash
$ flask run
* Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

For deployment use a appropiate webserver (e.g. Gunicorn).