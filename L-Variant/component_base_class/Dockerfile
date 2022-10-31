# set base image (host OS)
FROM python:3.9

# set the working directory in the container
WORKDIR /test

# copy the dependencies file to the working directory
COPY ./requirements.txt /test/requirements.txt

# install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY / /test

# command to run on container start
ENTRYPOINT [ "python", "component_base_class_test.py" ]