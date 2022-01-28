FROM python:3.7-slim

# set the working directory in the container
RUN mkdir -p /app
WORKDIR /app

# copy the dependencies file to the working directory
COPY requirements.txt requirements.txt

# install dependencies
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY / .

HEALTHCHECK --interval=10s --timeout=10s --start-period=30s --retries=3 \
    CMD pidof python3 || exit 1

CMD ["python","anonymizer.py","worker", "-l", "info"]
