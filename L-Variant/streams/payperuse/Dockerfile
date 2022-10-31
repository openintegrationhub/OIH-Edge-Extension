FROM python:3.9
    
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

#CMD ["faust", "-A","payperuse", "worker", "-l", "info"]
CMD ["python","payperuse.py","worker", "-l", "info"]
#CMD ["python","payperuse.py"]