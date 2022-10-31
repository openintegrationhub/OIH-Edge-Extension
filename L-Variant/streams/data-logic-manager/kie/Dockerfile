FROM jboss/kie-server:7.46.0.Final

####### Drools KIE Server CUSTOM CONFIGURATION ############
RUN mkdir -p $HOME/.m2
ADD standalone-full-kie-server.xml $JBOSS_HOME/standalone/configuration/standalone-full-kie-server.xml
ADD kie-server-users.properties $JBOSS_HOME/standalone/configuration/kie-server-users.properties
ADD kie-server-roles.properties $JBOSS_HOME/standalone/configuration/kie-server-roles.properties
ADD start_kie-server.sh $JBOSS_HOME/bin/start_kie-server.sh
ADD settings.xml $JBOSS_HOME/../.m2/settings.xml

# Added files are chowned to root user, change it to the jboss one.
USER root
RUN  chmod +x $JBOSS_HOME/standalone/configuration/standalone-full-kie-server.xml && \
chmod +x $JBOSS_HOME/standalone/configuration/kie-server-users.properties && \
chmod +x $JBOSS_HOME/standalone/configuration/kie-server-roles.properties && \
chmod +x $JBOSS_HOME/bin/start_kie-server.sh && \
chmod +x $JBOSS_HOME/../.m2/settings.xml

####### JBOSS USER ############
# Switchback to jboss user
USER jboss

####### RUNNING KIE-SERVER ############
WORKDIR $JBOSS_HOME/bin/
CMD ["./start_kie-server.sh"]