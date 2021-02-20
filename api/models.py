import datetime
import random

import flask
import flask_sqlalchemy
import flask_restless

import config

# Create the Flask application and the Flask-SQLAlchemy object.
app = flask.Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = config.PG_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = flask_sqlalchemy.SQLAlchemy(app)

class Schema():
    __table_args__ = {
        'schema': 'dummy'
    }

class Control(Schema, db.Model):
    pin = db.Column(db.String, primary_key=True)
    sensor = db.Column(db.String)
    data_type = db.Column(db.String)
    device_type = db.Column(db.String)
    value = db.Column(db.Float)
    __table_args__ = (db.UniqueConstraint(sensor, data_type),)

class SensorReadings(Schema, db.Model):
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, primary_key=True)
    temperature = db.Column(db.Float, default=-100)
    humidity = db.Column(db.Float, default=-100)
    # moisture_reading = db.Column(db.Float, default=-100)
    # moisture_pct = db.Column(db.Float, default=-100)
    temperature_status = db.Column(db.Boolean)
    humidity_status = db.Column(db.Boolean)
    fan_status = db.Column(db.Boolean)

# Control.__table__.drop(db.engine)
# SensorReadings.__table__.drop(db.engine)
db.create_all()

def is_token_valid(token):
    return token in config.VALID_TOKENS

def token_auth(**kwargs):
    if 'authToken' not in flask.request.headers:
         raise flask_restless.ProcessingException(code=402)
    if not is_token_valid(flask.request.headers['authToken']):
         raise flask_restless.ProcessingException(code=401)

# Create the Flask-Restless API manager.
preprocessors = {'POST':[token_auth]} #'GET_COLLECTION': [token_auth], 
manager = flask_restless.APIManager(app, flask_sqlalchemy_db=db, preprocessors=preprocessors)

# Create API endpoints, which will be available at /api/<tablename>
manager.create_api(SensorReadings, methods=['GET', 'POST', 'DELETE'])

# start the flask loop
app.run(host='192.168.0.176', debug=False)