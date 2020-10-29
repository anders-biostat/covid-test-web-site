## Virtual Environment

It is highly recommended to use a virtual environment
for the installation of the application.

### Prerequisites  

If you do not have python3-virtualenv installed please install it
beforehand.

Example for Debian based Linux Distributions:
```bash
$ sudo apt-get install python3-venv 
```

### Installation

It is recommended to install the virtual environment in the
project directory. For installing use the following command:

```bash
$ python3 -m venv venv
```

This creates a `venv` directory inside the project directory.
Please do not commit the `venv` directory to the repository.

### Activation and usage

For activation you can run the following command in the project
directory:

```bash
$ . venv/bin/activate
(venv) $
```

Now the virtual environment is activated. You can install packages
with the `pip` commands as usual (you dont have to use `pip3` as
the environment knows which python you are using).

To install the application requirements simply execute:

```bash
$ pip install -r requirements.txt
``` 