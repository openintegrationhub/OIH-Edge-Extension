# README #

### What is this repository for? ###

This is for uat environment ONLY for now. It's based on the official showcase image.
It comes out of the box with some default configuration(eg users, roles, etc).
The final version should be customized and that customization should be in Dockerfile.


### How do I get set up? ###

Just build the docker image. Again the Dockerfile is simple but we intend to put more there.
This is in case you are wondering why not using directly the official image.
```
docker build -t my-workbench .
```

Start by running 
```
docker run -p 8080:8080 -p 8001:8001 -d --name drools-workbench my-workbench:latest

```

Go to 
```
http://localhost:8080/business-central/
```
and login using one of the users available. 

### Who do I talk to? ###

For more information reach Sergiu Oltean or go to https://hub.docker.com/r/jboss/drools-workbench-showcase