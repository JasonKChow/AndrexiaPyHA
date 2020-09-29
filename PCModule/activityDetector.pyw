from pynput.mouse import Listener as mListener
from pynput.keyboard import Listener as kListener
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
from time import time
from psutil import process_iter, Process, wait_procs
from infi.systray import SysTrayIcon
from threading import Thread
from queue import Queue
import json


def onActivity(*args):
    mqttQ.put({'topic': 'desktop/activity', 'payload': time()})


def mqttWorker():
    while True:
        item = mqttQ.get()

        # Publish, wait for finish to keep going
        pub = client.publish(topic=item['topic'], payload=item['payload'])
        pub.wait_for_publish()

        mqttQ.task_done()


def starter():
    global mouseListener
    global kbListener

    if not (mouseListener.running or kbListener.running):
        client.publish('info/Living Room/lightOverride', payload=False)
        print('Starting on request')
        mouseListener = mListener(on_click=onActivity)
        kbListener = kListener(on_press=onActivity)
        mouseListener.start()
        kbListener.start()
        systray.update(icon=onImage)
        systray.update(hover_text='Activity Detector On')


def stopper():
    if mouseListener.running or kbListener.running:
        client.publish('info/Living Room/lightOverride', payload=True)
        print('Stopping on request')
        mouseListener.stop()
        kbListener.stop()
        systray.update(icon=offImage)
        systray.update(hover_text='Activity Detector Off')


def onQuit():
    client.disconnect()
    exit()


# Import config
with open('config.json') as file:
    config = json.load(file)

# Tray icons
onImage = 'activityDetectorOn.ico'
offImage = 'activityDetectorOff.ico'

# Create queue
mqttQ = Queue()

# Create threads
mouseListener = mListener(on_click=onActivity)
kbListener = kListener(on_press=onActivity)
mqttThread = Thread(target=mqttWorker, daemon=True)

# Create mqtt connection
client = mqtt.Client()
client.username_pw_set('jason')
client.will_set('info/Living Room/lightOverride', payload=False)

# Initialize with current time
curTime = time()
lastActive = [0]

# Create system tray
menuOptions = (('Start', None, starter), ("Stop", None, stopper),)
systray = SysTrayIcon(onImage, 'Activity Detector On', menuOptions,
                      on_quit=onQuit)

# Start everything!
systray.start()
mouseListener.start()
kbListener.start()
mqttThread.start()
client.connect(config['mqttIP'])
client.loop_forever()
