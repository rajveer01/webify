#!/bin/sh
# ---------------------------------------------------------------------------
# SYSTEMi Copyright ? 2000-2003, MetricStream, Inc. All rights reserved.
# Author Anand (aviswanath@metricstream.com)
# Created 12/12/2006
# $Id: Tomcat.MASTER.sh,v 1.1.2.3.2.1 2008-12-21 15:43:10 anilj Exp $
#
# Script for Staring and Stoping Tomcat service
# ---------------------------------------------------------------------------

SI_HOME=/opt/MetricStream/SYSTEMi
TOMCAT_HOME=$SI_HOME/Tomcat
JRE_HOME=$SI_HOME/Jre
PATH="$JRE_HOME/bin:$PATH"
export PATH

currentDir=`pwd`
cd $SI_HOME

TOMCAT_XMS=1G
TOMCAT_XMX=14G

ARGS="-server -XX:MaxPermSize=512m -XX:+HeapDumpOnOutOfMemoryError
-Xloggc:${SI_HOME}/Systemi/log/gc.log
-XX:CMSInitiatingOccupancyFraction=60 
-XX:NewRatio=3
-XX:+PrintGCDetails
-XX:+PrintGCDateStamps 
-XX:+PrintGCTimeStamps
-XX:+PrintGCCause
-XX:-PrintTenuringDistribution
-XX:+UseGCLogFileRotation
-XX:NumberOfGCLogFiles=5
-XX:GCLogFileSize=2M
-Doracle.jdbc.maxCachedBufferSize=24
-Duser.language=en -Duser.country=US -Dfile.encoding=UTF-8 -Xms$TOMCAT_XMS -Xmx$TOMCAT_XMX -Djava.awt.fonts=$JRE_HOME/lib/fonts -Dcatalina.base=$TOMCAT_HOME -Dcatalina.home=$TOMCAT_HOME -Djava.io.tmpdir=$TOMCAT_HOME/temp -Djava.util.logging.manager=org.apache.juli.ClassLoaderLogManager -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=$SI_HOME/Tomcat/logs -Djava.util.logging.config.file=$TOMCAT_HOME/conf/logging.properties  -DMETRICSTREAM.CONFIG=/opt/MetricStream/SYSTEMi/Systemi/Config/config.client.xml -DMETRICSTREAM.PROPERTY.NODE_ID=1  -Djava.security.policy=/opt/MetricStream/SYSTEMi/Systemi/Config/ecp-app.policy -Dlogback.configurationFile=/opt/MetricStream/SYSTEMi/Systemi/Config/logback.xml -Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false -Djava.security.auth.login.config=$SI_HOME/Systemi/Config/jaas.config -Dcom.sun.management.jmxremote.login.config=JaasLogin -Djmx.remote.x.login.config=JaasLogin -Dcom.sun.management.jmxremote.port=8888 -DMETRICSTREAM.HOME=$SI_HOME/Systemi -Djava.endorsed.dirs=$TOMCAT_HOME/common/endorsed -Djava.awt.headless=true -Duser.dir=$TOMCAT_HOME -Djava.security.egd=file:/dev/urandom"
JAVA_FONTS=$JRE_HOME/lib/fonts
export JAVA_FONTS
props="8269 8269 8269"
installation="worker1"

case "$1" in
'start')

if [ "$installation" = "worker1" ] ; then
echo "Starting Tomcat .."
nohup $JRE_HOME/bin/java $ARGS -jar "$TOMCAT_HOME/bin/bootstrap.jar" -config "$TOMCAT_HOME/conf/server.xml" start >>"$TOMCAT_HOME/logs/stdout.$(date +"%Y-%m-%d_%H%M%S").log" 2>>"$TOMCAT_HOME/logs/stderr.$(date +"%Y-%m-%d_%H%M%S").log" &
echo "Tomcat Service Starting up ..."
echo "Please check the log files to ensure server start before accessing the server."

else

echo "Starting Load Balanced Tomcat Services .."
for i in $props
do
    nohup $JRE_HOME/bin/java $ARGS -jar "$TOMCAT_HOME/bin/bootstrap.jar" -config "$TOMCAT_HOME/conf/server$i.xml" start >> "$TOMCAT_HOME/logs/stdout$i.$(date +"%Y-%m-%d_%H%M%S").log" 2>> "$TOMCAT_HOME/logs/stderr$i.$(date +"%Y-%m-%d_%H%M%S").log" &
done
echo "Tomcat Services Staring up ..."
echo "Please check the log files to ensure server start before accessing the server."

fi
;;

'stop')

if [ "$installation" = "worker1" ] ; then

    echo "Stoping Tomcat ..."
    nohup java $ARGS -jar "$TOMCAT_HOME/bin/bootstrap.jar" -config "$TOMCAT_HOME/conf/server.xml" stop >>"$TOMCAT_HOME/logs/stdout.$(date +"%Y-%m-%d_%H%M%S").log" 2>>"$TOMCAT_HOME/logs/stderr.$(date +"%Y-%m-%d_%H%M%S").log" &

else

    echo "Stoping Tomcat services ..."
    for i in $props
    do
        rm "$TOMCAT_HOME/conf/server.xml"
        cp "$TOMCAT_HOME/conf/server$i.xml" "$TOMCAT_HOME/conf/server.xml"
        nohup java $ARGS -jar "$TOMCAT_HOME/bin/bootstrap.jar" -config "$TOMCAT_HOME/conf/server$i.xml" -debug stop >>"$TOMCAT_HOME/logs/stdout$i.$(date +"%Y-%m-%d_%H%M%S").log" 2>>"$TOMCAT_HOME/logs/stderr$i.$(date +"%Y-%m-%d_%H%M%S").log" &
    done

fi

echo "Done"
;;

*)

echo "Usage : \"$0 [ start | stop ]"
echo "start - To start the Tomcat Services"
echo "stop - To stop the Tomcat Services"
;;

esac

cd $currentDir
exit 0
