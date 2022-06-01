from pydantic import BaseModel

from app.model._base import db, ConstrainedIntMongo

sensors_table = db['sensors']


class Sensor(BaseModel):
    sensorId: ConstrainedIntMongo
    hardwareVersion: str
    softwareVersion: str