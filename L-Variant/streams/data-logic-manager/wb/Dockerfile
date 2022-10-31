FROM jboss/drools-workbench:7.18.0.Final

ENV KIE_SERVER_PROFILE standalone-full-drools
ENV JAVA_OPTS -Xms256m -Xmx2048m -Djava.net.preferIPv4Stack=true -Dfile.encoding=UTF-8

####### Drools Workbench CUSTOM CONFIGURATION ############
ADD standalone-full-drools.xml $JBOSS_HOME/standalone/configuration/standalone-full-drools.xml
ADD drools-users.properties $JBOSS_HOME/standalone/configuration/drools-users.properties
ADD drools-roles.properties $JBOSS_HOME/standalone/configuration/drools-roles.properties
ADD start_drools-wb.sh $JBOSS_HOME/bin/start_drools-wb.sh


# Added files are chowned to root user, change it to the jboss one.
USER root
RUN chmod +x $JBOSS_HOME/standalone/configuration/standalone-full-drools.xml && \
chmod +x $JBOSS_HOME/standalone/configuration/drools-users.properties && \
chmod +x $JBOSS_HOME/bin/start_drools-wb.sh && \
chmod +x $JBOSS_HOME/standalone/configuration/drools-roles.properties

# Switchback to jboss user
USER jboss

####### RUNNING DROOLS-WB ############
WORKDIR $JBOSS_HOME/bin/
CMD ["./start_drools-wb.sh"]