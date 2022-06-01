import pymongo as pymongo
from pydantic.types import conint

from configuration import DB_LINK

client = pymongo.MongoClient(DB_LINK)
db = client["test"]
MONGODB_INT_UPPER_LIM = 2 ** 31
ConstrainedIntMongo = conint(gt=0, lt=MONGODB_INT_UPPER_LIM)