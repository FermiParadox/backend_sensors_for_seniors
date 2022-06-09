from pydantic import BaseModel

from app.model._base import ConstrainedIntMongo


class SensorAssignment(BaseModel):
    seniorId: ConstrainedIntMongo
    sensorId: ConstrainedIntMongo
