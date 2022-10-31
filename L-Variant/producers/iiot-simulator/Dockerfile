FROM python:3.9.1-alpine AS wheels

WORKDIR /app
COPY requirements.txt /app
RUN apk add --no-cache gcc g++ && \
    pip wheel --wheel-dir=/root/wheels -r requirements.txt

##################################
# set base image (host OS)
FROM python:3.9.1-alpine

# set the working directory in the container
WORKDIR /app

# copy the dependencies file to the working directory
COPY requirements.txt /app
COPY --from=wheels /root/wheels /root/wheels
RUN apk add --no-cache libstdc++ libpq && \
    pip install --no-index --find-links=/root/wheels -r requirements.txt

COPY . /app
RUN pip install -r requirements.txt


# copy the content of the local src directory to the working directory
COPY . /app
COPY configs/config.json /app/configs/config.json
COPY configs/logging.yml /app/configs/logging.yml

HEALTHCHECK --interval=10s --timeout=10s --start-period=30s --retries=3 \
    CMD pidof python3 || exit 1

CMD ["python3", "iiotsimulator.py"]
