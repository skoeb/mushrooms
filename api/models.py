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

class SensorReadings(Schema, db.Model):
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, primary_key=True)
    rand = db.Column(db.Integer, default=random.randint(0,1e6))

SensorReadings.__table__.drop(db.engine)
db.create_all()

# --- create dummy data with ORM ---
for i in range(10):
    new = SensorReadings()
    db.session.add(new)
    db.session.commit()

# Create the Flask-Restless API manager.
manager = flask_restless.APIManager(app, flask_sqlalchemy_db=db)

# Create API endpoints, which will be available at /api/<tablename>
manager.create_api(SensorReadings, methods=['GET', 'POST', 'DELETE'])

# start the flask loop
app.run(host='192.168.0.176')
