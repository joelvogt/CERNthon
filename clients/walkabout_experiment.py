# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
from collections import deque
from json import dumps, loads

from walkabout.base.client import import_module


class ExperimentProducer(object):
    mqtt_server = 'test.mosquitto.org'
    walkabout_server = 'localhost'
    walkabout_module = 'mqtt_producer'
    task = 'experiment'

    def __init__(self, experiment_label, timerate):
        self.mqtt_producer = import_module(ExperimentProducer.walkabout_module)
        self.label = experiment_label
        self.timerate = timerate
        self.frame_buffer = deque()
        self.frame_id = -1
        self.header = None
        self.topic = '%(task)s/%(label)s' % dict(
            task=ExperimentProducer.task,
            label=self.label)

    def send_frames(self):
        f_frame_buffer_pop_left = self.frame_buffer.popleft
        message = dumps([f_frame_buffer_pop_left() for i in range(len(self.frame_buffer))])
        self.mqtt_producer.single(self.topic,
                                  message,
                                  hostname=ExperimentProducer.mqtt_server)

    def add_frame(self, raw_frame):
        frame = raw_frame.split()
        if len(frame) == 0:
            frame = [raw_frame]
        first_item = frame[0]

        if self.frame_id == -1: #Header data, frame data starts at 0
            self.frame_buffer.append(frame)
            if ord(first_item[0]) >= ord('0') and ord(first_item[0]) <= ord('9'): #it's a frame number. Done processing the header
                self.frame_id = int(first_item[0])
                self.header = self.frame_buffer[-2]
                self.frame_buffer.clear()
        else:
            frame_object = dict(zip(self.header, frame))
            self.frame_buffer.append(frame_object)
            if self.frame_id != first_item and (int(first_item) % self.timerate) == 0:
                self.frame_id = first_item
                self.send_frames()

    def close(self):
        self.frame_buffer.append(b'EOF')
        self.send_frames()


try:
    import paho.mqtt.client as mqtt

    class ExperimentConsumer(object):
        mqtt_server = 'test.mosquitto.org'
        task = 'experiment'

        def __init__(self, experiment_label, frame_action):
            self.frame_action = frame_action
            self.label = experiment_label
            self.topic = '%(task)s/%(label)s' % dict(
                task=ExperimentConsumer.task,
                label=self.label)
            self.client = mqtt.Client()
            self.client.on_connect = lambda client, userdata, flags, rc: client.subscribe(self.topic)
            self.client.on_message = self.on_message

        def on_message(self, client, userdata, msg):
            topic = msg.topic
            messages = loads(msg.payload.decode())
            for frame in messages:
                if frame == 'EOF':
                    if hasattr(self.frame_action, 'close'):
                        self.frame_action.close()
                        break
                else:
                    self.frame_action(topic, frame)

        def listen(self):
            self.client.connect(ExperimentConsumer.mqtt_server)
            self.client.loop_forever()


    class FrameAction(object):
        """Action objects on frame should be callable and have a close function.
        Otherwise just use a  function"""

        def __call__(self, topic, frame):
            assert NotImplementedError

        def close(self):
            assert NotImplementedError
except ImportError:
    pass