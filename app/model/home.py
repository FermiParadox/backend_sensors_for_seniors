from enum import Enum

from pydantic import BaseModel

from app.model._base import db, ConstrainedIntMongo

homes_table = db['homes']


class HomeTypes(str, Enum):
    nursing = "NURSING"
    private = "PRIVATE"


class Home(BaseModel):
    homeId: ConstrainedIntMongo
    name: str
    type: HomeTypes