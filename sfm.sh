#!/usr/bin/env sh

#Place this file in /home/sfm and use crontab -e and enter:
#the 30 sec sleep is to wait until network services are up before firebase_listener
# or authentication will fail
#
#@reboot sleep 30 && /bin/sh /home/sfm/sfm.sh >/dev/null 2>&1


#get the current date/time
dt=$(date '+%m/%d/%Y %H:%M:%S');

#All controller scrips are located here:
cd /home/sfm

#kill all node and python processes (if any)
#There cannot be multiple instances of the controller running
echo "$dt - Terminating old Controller processes" >> /home/sfm/sfm.log
killall -qw node
killall -qw python



#Run script
#node.js binary is located at /usr/local/bin
#The node firebase_listener.js will spawn the python controller
/usr/local/bin/node /home/sfm/firebase_listener.js &  >>  /home/sfm/sfm.log
echo "$dt - Controller restarted" >> /home/sfm/sfm.log
