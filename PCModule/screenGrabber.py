from PIL import ImageGrab, ImageEnhance, Image
import numpy as np
from time import sleep
import paho.mqtt.client as mqtt
import json
from pynput import keyboard as kb
from threading import Thread
from queue import Queue
from time import time


def kbWorker():
    topic = 'desktop/color'

    # Send element color and last color with delay
    lastSend = 0
    while True:
        item = kbQ.get()

        if item == kb.Key.f1:
            # Fire
            curTime = time()
            if curTime - lastSend > 0.25:
                mqttQ.put_nowait({'topic': topic, 'payload': '[255, 0, 0]',
                                 'revert': True, 'delay': .25})
                lastSend = curTime
        elif item == kb.Key.f2:
            # Water
            curTime = time()
            if curTime - lastSend > 0.25:
                mqttQ.put_nowait({'topic': topic, 'payload': '[0, 157, 255]',
                                 'revert': True, 'delay': .25})
                lastSend = curTime
        elif item == kb.Key.f3:
            # Air
            curTime = time()
            if curTime - lastSend > 0.25:
                mqttQ.put_nowait({'topic': topic, 'payload': '[179, 0, 255]',
                                  'revert': True, 'delay': .25})
                lastSend = curTime
        elif item == kb.Key.f4:
            # Earth
            curTime = time()
            if curTime - lastSend > 0.25:
                mqttQ.put_nowait({'topic': topic, 'payload': '[255, 200, 0]',
                                  'revert': True, 'delay': .25})
                lastSend = curTime

        kbQ.task_done()


def mqttWorker():
    while True:
        item = mqttQ.get()

        # Publish, wait for finish to keep going
        pub = client.publish(topic=item['topic'], payload=item['payload'])
        pub.wait_for_publish()

        # Delay if needed
        if 'delay' in item:
            sleep(item['delay'])

        # Revert back to previous color if needed
        if 'revert' in item and item['revert']:
            rgbJSON = json.dumps(lastRGBs.tolist())
            pub = client.publish(topic=item['topic'], payload=rgbJSON)
            pub.wait_for_publish()

        mqttQ.task_done()


# Import config
with open('config.json') as file:
    config = json.load(file)

# Create queues
kbQ = Queue()
mqttQ = Queue()

# Enhancement
enhancement = 'pilColor'

# Send information to mqtt
client = mqtt.Client()
client.username_pw_set('jason')
client.will_set('desktop/colour', payload=False)
client.connect(config['mqttIP'])
client.loop_start()

kbListener = kb.Listener(on_press=lambda key: kbQ.put_nowait(key))
kbListener.start()

kbThread = Thread(target=kbWorker, daemon=True)
kbThread.start()
mqttThread = Thread(target=mqttWorker, daemon=True)
mqttThread.start()

keepGoing = True
lastRGBs = np.array([0, 0, 0])
while keepGoing:
    # Get screen
    screen = ImageGrab.grab()

    # Enhance colors
    if enhancement == 'pilColor':
        enhancer = ImageEnhance.Color(screen)
        screen = enhancer.enhance(4)
    elif enhancement == 'manual':
        screen = screen.convert('HSV')
        screen = np.array(screen)
        screen[:, :, 1] += 10
        screen = Image.fromarray(screen, 'HSV')
        screen = screen.convert('RGB')

    # Convert to array of average RGB values to send
    screen = np.array(screen)
    screen = np.mean(screen, axis=(0, 1))

    # Shut off lights for black
    # screen = screen if np.sum(screen) > 150 else np.array([0, 0, 0])

    # Send if different than last check
    if np.sum(np.abs(screen - lastRGBs)) > 15:
        rgbJSON = json.dumps(screen.tolist())
        mqttQ.put_nowait({'topic': 'desktop/color', 'payload': rgbJSON})
        print(rgbJSON)

    # Save for next time
    lastRGBs = screen

    # Wait for a bit
    sleep(.25)
