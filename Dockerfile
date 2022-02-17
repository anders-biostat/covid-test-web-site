# Select Python 3.8.12 Base-Image
FROM python:3.8.12-alpine
ENV PYTHONUNBUFFERED 1

# Select workdir
ENV APP_ROOT /project
WORKDIR ${APP_ROOT}

RUN mkdir -p ${APP_ROOT}/static
RUN mkdir -p ${APP_ROOT}/media

# Set the working directory to /project
WORKDIR ${APP_ROOT}

# Copy the current directory contents into the container at /project
ADD covidtest ${APP_ROOT}

# Copy the local .env file to the project root
ADD .env ${APP_ROOT}

# Copy git directory to project (for version displaying)
ADD .git ${APP_ROOT}/.git

# Install dependencies
COPY requirements.txt ${APP_ROOT}/requirements.txt

RUN apk update && \
    apk add --virtual build-deps gcc python3-dev musl-dev libffi-dev && \
    apk add postgresql-dev && \
    apk add netcat-openbsd && \
    apk add gettext && \
    apk add zlib-dev jpeg-dev && \
    pip3 install -U pip && \
    pip3 install -r ${APP_ROOT}/requirements.txt && \
    pip3 install psycopg2 && \
    chmod 775 -R ${APP_ROOT} && \
    python3 ./manage.py migrate

# Command for testing the server
CMD python ./manage.py collectstatic --noinput
