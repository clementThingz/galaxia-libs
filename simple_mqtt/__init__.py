import adafruit_minimqtt.adafruit_minimqtt as MQTT
import ssl
import supervisor

class SimpleMQTT:

    def __init__(self, username, password, broker, port, socketpool, onConnect, onDisconnect, onMessage):
        self.user_on_connect = onConnect
        self.user_on_disconnect = onDisconnect
        self.user_on_message = onMessage
        self.client = MQTT.MQTT(
            broker=broker,
            port=port,
            username=username,
            password=password,
            socket_pool=socketpool,
            ssl_context=ssl.create_default_context()
        )
        self.topics = {}
        self.mutex = False
        self.client.on_connect = lambda client, userdata, flags, rc: self.on_connect()
        self.client.on_disconnect = lambda client, userdata, rc: self.on_disconnect()
        self.client.on_message = lambda client, topic, message: self.on_message(client, topic, message)

    def process(self):
        #print("process")
        try:
            if self.mutex:
                return
            self.mutex = True
            if self.client.is_connected():
                self.client.loop(timeout=0.1)
            self.mutex = False
        except Exception as e:
            self.mutex = False
            if not  str(e).startswith("MiniMQTT is not connected"):
                print(e)

    def connect(self):
        self.client.connect()
        
        for topic in self.topics:
            self.client.subscribe(self.topics[topic][0])
        

    def subscribe(self, topic, cb=None):
        self.topics[str(hash(topic))] = [topic, cb]
        try:
            if self.client.is_connected():
                self.mutex = True
                self.client.subscribe(topic)
                self.mutex = False
        except MQTT.MMQTTException:
            self.mutex = False

    def publish(self, topic, value):
        try:
            self.mutex = True
            self.client.publish(topic, value)
            self.mutex = False
        except MQTT.MMQTTException:
            self.mutex = False

    def is_connected(self):
        return self.client.is_connected()

    def on_connect(self):
        self.user_on_connect()

    def on_disconnect(self):
        self.user_on_disconnect()

    def on_message(self, client, topic, message):
        h = str(hash(topic))
        if h in self.topics and self.topics[h] != None and self.topics[h][1] != None:
            self.topics[h][1](message)
        else:
            self.user_on_message(topic, message)


def version():
    return "1.0.5"