from paho.mqtt import client as mqtt_client
import digi
import json

# Debug flag to toggle more verbose logging
DEBUG = False

# Connection will only resolve if digi is running in Kubernetes cluster.
# Will not work in digi test mode.
broker = 'emqx'
port = 1883

def connect_mqtt(username, password) -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            digi.logger.info("Connected to digi MQTT broker")
        else:
            digi.logger.info(f"Failed to connect to digi MQTT broker, return code {rc}")

    # Client ID - used for tracking subscriptions; must be unique
    client = mqtt_client.Client(digi.name + '-ingest')
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        data = msg.payload.decode()
        topic = msg.topic

        if DEBUG: digi.logger.info(f"New message on topic {topic}:\n{data}")

        try:
            data_json = json.loads(data)
            digi.pool.load([data_json])
        except json.JSONDecodeError:
            digi.logger.error("Message was not in JSON format, ignoring")

    # Listen on digi's name as the topic
    client.subscribe(digi.name)
    client.on_message = on_message

    digi.logger.info(f"Listening for messages on topic {digi.name}")

def start_listening(username="admin", password="digi_password"):
    client = connect_mqtt(username, password)
    subscribe(client)
    client.loop_forever()
