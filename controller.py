
#This file is spawned by firebase-listener.js
# https://www.sohamkamani.com/blog/2015/08/21/python-nodejs-comm/

import sys
from subprocess import call
from threading import Timer
from threading import Thread
import paho.mqtt.client as mqtt
from datetime import datetime

# import RPi.GPIO as GPIO
import time
#import spidev


# Credentials required by MQTT moquitto broker
# MQTT Broker is a linux service that should start automatically on boot
from mqtt_credentials import *

##################################
# TODO
##################################
# set this to primary or backup
# the two controllers should monitor each other with keepalives
# and switch roles when detecting a failure
mqttClientId = "NODE-controller"

# siteId is provided by firebase as a reply to a hello message
siteId = "TEST"
# nodeId and wanIp are provided by the node on a hello message
nodeId = "NO_NODEID"
wanIp = "none"



mqttTopicMaxLength = 50
mqttMsgMaxLength = 50



# Send mqtt commands to node to turn on or off a particular relay
def relayControl(cmd):
    if cmd[0] != "SWITCH":
        return
    nodeId = cmd[1]
    ###
    #togle single relay
    if cmd[3]=="s": #Single relay command
        relay = cmd[4] # relay number
        rlState = 1 if cmd[2]=='true' else 0 #0= Off, 1= On
        mqttPub(nodeId, "relay/" + str(relay), str(rlState))
    ###
    #On and Off push buttons (using two relays for contactors)
    elif cmd[3] == "p": #Pulse one of the two-relay set on and then off
        rlState = 1 if cmd[2]=='true' else 0 #0= Off, 1= On
        relay = cmd[4] if rlState else cmd[5] #on = first relay, off = second relay
        pulse(nodeId, relay)

#Turns a relay on for 1 second, then off
def pulse(nodeId, relay):
    def off(relay):
        mqttPub(nodeId, "relay/" + str(relay), str(0)) #turn relay off
    mqttPub(nodeId, "relay/" + str(relay), str(1)) #turn on
    t = Timer(1, off, [relay])
    t.start();





# callback to get mqtt messages received
def on_message(client, userdata, message):
    print("Message received: ")
    # print("message topic=",message.topic)
    # print("message qos=",message.qos)
    # print("message retain flag=",message.retain)
    topicKeys = parse_topic(message.topic)
    for i, element in enumerate(topicKeys):
        print ("key", i, element)

    payload = str(message.payload.decode("utf-8"))

    # print ("Payload: ", str(message.payload.decode("utf-8")))
    print ("Payload: ", payload)

    nodeId = topicKeys[1] #This will be true for all messages published by nodes

    # Handle HELLO message
    # If WAN IP is associated to a siteId -> send siteId to node and add/update node data in firebase
    # if WAN IP is unknown -> request node siteId (payload '?')
    if (str(topicKeys[0]) == 'hello'):
        nodeId = topicKeys[1]
        print("HELLO: NODE id " , nodeId)
        time.sleep(0.1) #delay to allow wifi node to receive mqtt immediately after sending hello

        # VERIFY THE NODE IS SENDING THE WAN IP AS PAYLOAD!!
        wanIp = str(message.payload.decode("utf-8"))
        print("wanIp from hello: ", wanIp)

        ##vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        # QUERY FIREBASE IF WAN IP IS ASSOCIATED TO A SITE ID
        #use dbSend(key, value)
        # dbSend('Sent to stdout the WAN IP!', wanIp)
        ##^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


        #SEND THE SITE ID TO THE NODE IF KNOWN, OTHERWISE NODE SHOULD PROMPT USER FOR SITE ID
        mqttPub(nodeId, 'siteId', 'ABCDEFGHI')
        # mqttPub(nodeId, 'siteId', '?') #Example to get current setting

        # ONCE THE NODE HAS THE CORRECT SITE ID, IT SHOULD SEND A NEW HELLO TO THE SITEID (CONTROLLER)
        # THEN THE CONTROLLER SHOULD UPDATE FIREBASE WITH THE NODE STATUS, SETTINGS AND CAPABILITIES
        # THEN FIREBASE SHOULD UPDATE SETTINGS FOR MASTER, BACKUP AND SITE CONTROLLERS
        # THEN THE NODE SHOULD TEST ALL CONTROLLERS TO DETERMINE CONNECTIVITY

    # Record crash info
    elif (str(topicKeys[0]) == 'status'):

        nodeId = topicKeys[1]
        f = open("node_status.log", "a")
        f.write(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
        f.write(' >>> ')
        f.write(nodeId)
        f.write(' : ')
        f.write(payload)
        f.write("\n")
        f.close()



def on_connect(client, userdata, flags, rc):
    if rc==0:
        print("connected OK Returned code=",rc)
    else:
        print("Bad connection Returned code=",rc)

def on_log(client, userdata, level, buf):
    print("log: ",buf)


#function to split the topic by the '/'delimiter and return a list
def parse_topic(topic):
    #list returned will have:
    #TO (or hello), FROM, target, [index]
    return topic.split('/')



# create an instance of the mqtt client
mqttClient = mqtt.Client(mqttClientId)
mqttClient.username_pw_set(mqttUser, mqttPswd)

# for testing
#mqttClient.publish("topic/test", "Hello world!")

#callbacks
mqttClient.on_message = on_message #attach function to CALLBACK
mqttClient.on_log = on_log
mqttClient.on_connect = on_connect

mqttClient.connect("localhost")

mqttClient.loop_start() # starts mqtt callback loop to display published messages
time.sleep(4)  # time to process the callback
# mqttClient.subscribe("topic/test")
# mqttClient.subscribe("esp/test")
#mqttClient.publish("topic/test", "Hello world!")

### DEFINE THIS ON A SEPARATE HEADER FILE.
### NEEDS TO BE DIFFERENT FOR THE MASTER AND SITE CONTROLLERS
### PRIMARY/BACKUP SUBSCRIBE TO EVERYTHING
### SITE CONTROLLER ONLY SUBSCRIBES TO ITS SITEID
mqttClient.subscribe("#") #THIS IS ONLY FOR THE MASTER AND BACKUP CONTROLLERS!


def mqttPub(nodeId, key, value):
    #GET: Set value to '?' to GET status/config (stated in the topic) from the nodes
    #SET: Setting value to any other string will SET the topic parameter to that value.
    topic = str(nodeId) + '/' + str(key)
    value = str(value)
    # print("Topic: " + str(topic) + " - Topic Length: " + str(len(topic)) )
    # Verify Topic string is not longer than the max the node can accept
    if len(topic) > mqttTopicMaxLength:
        print(\
        "ALERT: mqtt TOPIC (" + str(topic) +") length (" + str(len(topic)) + \
        ") exceeds node limit (" + str(mqttTopicMaxLength) +  \
        ") and it will be truncated")

    # Verify payload/value string is not longer than the max the node can accept
    if len(value) > mqttMsgMaxLength:
        print(\
        "ALERT: mqtt PAYLOAD (" + str(value) +") length (" + str(len(value)) + \
        ") exceeds node limit (" + str(mqttMsgMaxLength) +  \
        ") and it will be truncated")

        # or len(value) > mqttMsgMaxLength:
    # call(["mosquitto_pub", "-t", topic, "-u", mqttUser, "-P", mqttPswd, "-m", value], shell = False)
    mqttClient.publish(topic, value)

def dbSend(key, value):
    '''
    function to send data to FIREBASE via stdout to node.js thread
    '''
    sys.stdout.flush()
    sys.stdout.write(key + ":" + str(value))
    sys.stdout.flush()
    # needs a small delay to allow time to flush
    time.sleep(.1)


def main():
    '''
    This loop runs on a separate thread (dataIn = Thread(target = main, args = ()) )
    and waits on the readline instruction until it receives something
    '''
    while 1:
        # Interface with the Node.js module is done via stdin messages
        # read messages from database listener
        line = sys.stdin.readline()
        #separate the key/value
        # status[0] = switch # ID
        # status[1] = switch state (see swState dictionary for valid replies)
        status = (line.strip().split(':'))

        #vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        ## FOR TEST ONLY.
        ##This will increase the size of a local file (message.txt)
        ## log the key/value (switch /state) received from firebase
        # f = open("message.txt", "a")
        # for arg in status:
        #     f.write(arg)
        #     f.write(' : ')
        # f.write("\n")
        # f.close()
        #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        # RELAY Control

        # Check if it is a relay control message
        if status[0] == "SWITCH":

            # f = open("message.txt", "a")
            # f.write("Relay Control for ")
            # f.write(status[1])
            # f.write("\n")
            # f.close()

            relayControl(status)

            # nodeId = status[1]
            # if status[3]=="s": #Single relay command
            #     relay = status[4] # relay number
            #     rlState = 1 if status[2]=='true' else 0 #0= Off, 1= On
            #     mqttPub(status[1], "relay/" + str(relay), str(rlState))
            #
            # elif status[3] == "p": #Pulse two relays for on/off
            #     rlState = 1 if status[2]=='true' else 0 #0= Off, 1= On
            #     relay = status[4] if rlState else status[5] #on = first relay, off = second relay
            #     pulse(nodeId, relay)





            # mqttPub(status[1], "relay/" + str(relay), str(rlState))


        # Using the swState.get to prevent an incorrect return value from causing an exception
        #setRelay(switches[status[0]], swState.get(status[1], swStateDefault))

        ### For testing function to turn on/off a relay
        # setRelay(16, 1)
        # time.sleep(2)
        # setRelay(16,0)


        ##this code shuts down the controller
        # elif status[0] == SW_5:
        #     if status[1] != 'false':
        #          call('sudo /sbin/shutdown -P now', shell = True)


# def readInput(channel):
#     adc = spi.xfer2([1,(8+channel)<<4,0])
#     data = ((adc[1]&3) << 8) + adc[2]
#     return data
#
#
# def sendOut(sensorId, value):
#     sys.stdout.write(sensorId + ":" + value)
#     sys.stdout.flush()
#     # needs a small delay to allow time to flush
#     time.sleep(.1)


#----------------------------------------------------
#----------------------------------------------------
#----------------------------------------------------
# SCRIPT STARTS HERE!
#----------------------------------------------------
#----------------------------------------------------
#----------------------------------------------------
#--------------------------------------
#--------------------------------------
#--------------------------------------
#Start main() in a separate thread to listen for stdin messages from node.js
dataIn = Thread(target = main, args = ())
dataIn.start()
#--------------------------------------
#--------------------------------------
#--------------------------------------

# GET HERE THE CURRENT STATUS OF ALL SWITCHES AND STORE THEM IN A dictionary
# ONLY PUBLISH AN MQTT MESSAGE TO NODE IF THE SWITCH STATE HAS CHANGED
# OR SHALL WE HAVE THE NODE DO THAT?




## FOR TESTING SENDING MESSAGES TO JAVASCRIPT
# for x in range (5):
#     dbSend("SFM", x)
#     time.sleep(1)


## Don't let this script end!!!
## otherwise it will teminate the spawned instance from node.js, with the error:
## Error [ERR_STREAM_DESTROYED]: Cannot call write after a stream was destroyed
while True:
    time.sleep(1)


#GET MQTT MESSAGES FROM NODES AND UPDATE FIREBASE
#mosquitto_sub -h localhost -p 1883 -t "esp/test" -u sfmNode -P 7VYSDEw92Zs -v

# mqttClient.publish("topic/test", "Hello world!")

# #read SPI sensors
# spi = spidev.SpiDev()
# spi.open(0,0)
# spi.max_speed_hz = 7629
#
# numberOfSamples = 3
# #!!numberOfSamples = 10
#
# numberOfSensors = 2
# previousSensorValue = [-1]*numberOfSensors
#
#
#
# while True:
#     readings = []
#     for n in range(numberOfSamples):
#         sample = []
#         for sensor in range(2):
#             rawValue = (readInput(sensor))
#
#             #-----------------------------
#             # Fore testing Only
#             #print str(sensor) + " : " + str(rawValue)
#             #-----------------------------
#
#             # convert ADC digital code to amps
#             #!! DO AMPS CONVERSION JUST ONCE AFTER THE AVERAGING! JUST APPEND SAMPLE RAW VALUES
#             sample.append(int (round(rawValue * sensorCorrection)))
#             #!!sample.append(rawValue)
#
#         readings.append(sample)
#         time.sleep(1)
#         #!!time.sleep(0.2)
#
#     # get the average of the readings
#     sensorAverageValue = [0]*numberOfSensors
#     samples = len(readings)
#     for reading in range(samples):
#         sensors = len(readings[reading])
#         for sensor in range(sensors):
#             sensorAverageValue[sensor] += readings[reading][sensor]
#
#     for sensor in range(numberOfSensors):
#         # Get the average
#         sensorAverageValue[sensor] /= 3
#         #!!sensorAverageValue[sensor] /= numberOfSamples
#         #convert to amps
#         sensorAverageValue[sensor] = int(round(sensorAverageValue[sensor] * sensorCorrection))
#
#
#     #print sensorAverageValue
#
#     # send sensor's readings to the node.js listener
#     for sensor in range(len(sensorAverageValue)):
#         #print "Channel "+str(i), " : "+ str(amps)
#
#         # Only update the database if the value has changed`
#         if (sensorAverageValue[sensor] != previousSensorValue[sensor]):
#             previousSensorValue[sensor] = sensorAverageValue[sensor]
#             sensorId = "c_" + str(sensor+1)
#             #map sensor to app switch
#             sensorId = mapSensorToSwitch[sensorId]
#
#             value = str(sensorAverageValue[sensor])
#             sendOut(sensorId, value)
