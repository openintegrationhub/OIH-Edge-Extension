# set base image (host OS)
FROM python:3.10

# set the working directory in the container
WORKDIR /opcua

# copy the dependencies file to the working directory
COPY ./requirements.txt /opcua/requirements.txt

# install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY / .

# command to run on container start
CMD [ "python", "opcua.py" ]