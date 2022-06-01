from typing import Optional

from pydantic import BaseModel

from app.model._base import db, ConstrainedIntMongo

seniors_table = db['seniors']


class Senior(BaseModel):
    seniorId: ConstrainedIntMongo
    name: str
    homeId: ConstrainedIntMongo
    enabled: bool
    sensorId: Optional[int] = 0