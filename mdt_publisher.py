import os
import shutil
import logging
import json

import logging
import logging.config

from argparse import ArgumentParser
from configparser import ConfigParser, ExtendedInterpolation

from kombu import BrokerConnection, Exchange, Producer

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

import settings

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = settings.TRACK_MODIFICATIONS

db = SQLAlchemy(app)

APP_NAME = "mdt-publisher"

class Greeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())

    def __repr__(self):
        return f"<Greeting {self.id} ({self.created_at})>"

def increment_greetings():
    db.session.add(Greeting())
    db.session.commit()

@app.route('/greetings')
def count_greetings():
    global db

    return {"greetings": db.session.query(func.count(Greeting.id)).scalar() }

@app.route('/')
def hello_world():
    increment_greetings()
    return 'MindNet Publisher!\r\n'

@app.route('/intent')
def send_intent():
    logger.info(f"Publishing intent")
    publish("intents")
    return "New intent has been published"

def publish(exchange):
    # Config file
    config = ConfigParser(interpolation=ExtendedInterpolation(), allow_no_value=True)
    config.read(f"/etc/opt/{APP_NAME}/config.ini")

    rabbit_ip = config.get("RABBITMQ", "ip")
    rabbit_port = config.getint("RABBITMQ", "port")
    rabbit_vhost = config.get("RABBITMQ", "vhost")
    rabbit_user = config.get("RABBITMQ", "user")
    rabbit_passw = config.get("RABBITMQ", "password")

    body = json.dumps(intent_example)

    conn = BrokerConnection(hostname=rabbit_ip, 
                            port=rabbit_port, 
                            userid=rabbit_user, 
                            password=rabbit_passw, 
                            virtual_host=rabbit_vhost, 
                            heartbeat=4)
    channel = conn.channel()
    exchange = Exchange(exchange, type='topic', durable=False)
    producer = Producer(exchange=exchange, channel=channel, routing_key=f'{exchange}.#')
    producer.publish(body)

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))

    # Creating app folder
    if not os.path.exists(f"/etc/opt/{APP_NAME}/"):
        os.mkdir(f'/etc/opt/{APP_NAME}/')

    # Copy default logging configuration file
    if not os.path.isfile(f"/etc/opt/{APP_NAME}/logconfig.ini"):
        shutil.copy(here + "/config/logconfig.ini", f'/etc/opt/{APP_NAME}/')

    # Copy default configuration file
    if not os.path.isfile(f"/etc/opt/{APP_NAME}/config.ini"):
        shutil.copy(here + "/config/config.ini", f'/etc/opt/{APP_NAME}/')

    # Creating logs folder
    if not os.path.exists(f"/var/log/{APP_NAME}/"):
        os.mkdir(f'/var/log/{APP_NAME}/')

    # Logging config file
    global logger
    logging.config.fileConfig(f"/etc/opt/{APP_NAME}/logconfig.ini")
    logger = logging.getLogger()

    app.run()

intent_example = \
{
  "Resources": [
    {
      "scopeId": "39D5EB05",
      "flowResourceId": "8633EC5A",
      "srcIP": "*",
      "tos": "1",
      "sense": "EGRESS",
      "resourceId": "B351FB6A",
      "resourceType": "FLOW_SAMPLE_SCOPE",
      "resourceAbstractionLayer": "0",
      "state": "ACTIVE",
      "changed": True
    },
    {
      "datapathType": "TC",
      "devicePortResourceId": "22222222",
      "deviceResourceId": "11111111",
      "iface": "eth0",
      "resourceId": "116CF756",
      "resourceType": "DATAPATH_POINT",
      "resourceAbstractionLayer": "0",
      "changed": True
    }
  ],
  "Intent": {
    "intentTargetResourceId": "B351FB6A",
    "intentTargetResourceType": "FLOW_SAMPLE_SCOPE",
    "intentTargetReferencePointId": "116CF756",
    "intentTargetReferencePointType": "DATAPATH_POINT",
    "actionName": "SET_PRIORITY",
    "resourceId": "DD069903",
    "resourceType": "INTENT",
    "resourceAbstractionLayer": "0",
    "reportedTime": 1608142766042,
    "changed": True
  },
  "Params": [
    {
      "paramOwnerResourceType": "INTENT",
      "paramOwnerResourceId": "DD069903",
      "paramName": "priority",
      "paramValue": "1",
      "paramSemantics": "HowToAction",
      "resourceId": "B8602F79",
      "resourceType": "PARAM",
      "resourceAbstractionLayer": "0",
      "reportedTime": 1608142766042,
      "changed": True
    }
  ]
}

