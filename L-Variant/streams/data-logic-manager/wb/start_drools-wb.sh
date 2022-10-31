#!/usr/bin/env bash

# Start Wildfly with the given arguments.
CUSTOM_ARGS=" -Dorg.kie.verification.disable-dtable-realtime-verification=true"

echo "Running Drools Workbench on JBoss Wildfly..."
exec ./standalone.sh -b $JBOSS_BIND_ADDRESS $CUSTOM_ARGS -c $KIE_SERVER_PROFILE.xml -Dorg.kie.demo=$KIE_DEMO -Dorg.kie.example=$KIE_DEMO
exit $?