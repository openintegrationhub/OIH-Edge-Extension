# README #

### What is this repository for? ###

This represents the Kie Server. It's basically the rules engine, though it can have more capabilities than rules.
Once we start this we can run the rules we create in the drools-workbench. We can start it embedded also in our application
but we lose the ability to develop rules faster. Once we create a rule in workbench we can deploy it on the KIE server and our
application will interact with it.

For a quick startup this is a pre-setup image with roles and users. This should be temporary and we need to revisit it.

### How do I get set up? ###

Just build the docker image. Again the Dockerfile is simple but we intend to put more there.
This is in case you are wondering why not using directly the official image.
```
docker build -t my-kie .
```

Start by running 

```
docker run -p 8180:8080 -d --name kie-server --link drools-wb:kie-wb my-kie:latest

```
drools-wb is the drools workbench container name. By linking them workbench can see all kie instances.


Go to 
```
http://localhost:8180/kie-server
```
and login using one of the users available. 

OR

assuming kie server deployed at 172.17.0.3
and workbench at 172.17.0.2
```
docker run -p 8180:8080 -d --name kie-server2 \
-e KIE_SERVER_LOCATION=http://172.17.0.3:8080/kie-server/services/rest/server \
-e KIE_SERVER_CONTROLLER=http://172.17.0.2:8080/business-central/rest/controller \
-e KIE_SERVER_CONTROLLER_USER=admin \
-e KIE_SERVER_CONTROLLER_PWD=admin \
-e KIE_SERVER_PWD=kieserver1! \
-e KIE_SERVER_USER=kieserver \
-e KIE_MAVEN_REPO=http://172.17.0.2:8080/business-central/maven2 \
-e KIE_MAVEN_REPO_USER=admin \
-e KIE_MAVEN_REPO_PASSWORD=admin \
my-kie:latest

```


### Who do I talk to? ###

For more information contact Sergiu Oltean or go to https://registry.hub.docker.com/r/jboss/kie-server-showcase.