import pymongo as pymongo
from fastapi import FastAPI, Path, HTTPException
from pydantic import BaseModel, validator, PositiveInt
from typing import Optional
from starlette import status
import uvicorn
from starlette.responses import JSONResponse

# MongoDB password
try:
    from app.IGNORE_GIT_SECRETS import PASS_MONGO_DB_USER0
except ImportError:
    print("The file containing the pass for the DB is not uploaded on Git. Please contact me for access.")
    PASS_MONGO_DB_USER0 = "NotTheRealPassword"


def _raise_http_422(msg):
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)


client = pymongo.MongoClient(
    f"mongodb+srv://user0:{PASS_MONGO_DB_USER0}@cluster0.4derf.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client["test"]

homes_table = db['homes']
sensors_table = db['sensors']
seniors_table = db['seniors']

ALLOWED_HOME_TYPES = {"NURSING", "PRIVATE"}


class Home(BaseModel):
    homeId: PositiveInt
    name: str
    type: str

    @validator("type")
    def type_allowed(cls, home_type):
        if not _is_allowed_home_type(home_type=home_type):
            _raise_http_422(msg=f"Home type can be either NURSING or PRIVATE ('{home_type}' not allowed).")
        return home_type


def _is_allowed_home_type(home_type):
    return home_type in ALLOWED_HOME_TYPES


class Sensor(BaseModel):
    sensorId: PositiveInt
    hardwareVersion: str
    softwareVersion: str


# TODO "Senior" -> "Patient"; "senior"/"sensor" too similar + hard to read; keep seniorId for clients as is
class Senior(BaseModel):
    seniorId: PositiveInt
    name: str
    homeId: PositiveInt
    enabled: bool
    sensorId: Optional[int] = 0

    @validator("homeId")
    def home_exists(cls, homeId):
        if not homes_table.find_one({"homeId": homeId}):
            _raise_http_422(
                msg=f"Can't assign senior to home ID {homeId} (home doesn't exist). Please try another one.")
        return homeId


app = FastAPI()


# TODO: consider removal (ask clarification); perhaps they want no GET to exist
@app.get("/homes")
def homes():
    return str(list(homes_table.find({})))


# TODO: consider removal (ask clarification); perhaps they want no GET to exist
@app.get("/seniors")
def seniors():
    return str(list(seniors_table.find({})))


# TODO: consider removal (ask clarification); perhaps they want no GET to exist
@app.get("/sensors")
def sensors():
    return str(list(sensors_table.find({})))


PATH_STORE_HOME = '/store-home/'


@app.post(PATH_STORE_HOME)
def store_home(newHome: Home):
    homes_table.insert_one(newHome.dict())
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=newHome.dict())


PATH_STORE_SENSOR = '/store-sensor/'


@app.post(PATH_STORE_SENSOR)
def store_sensor(newSensor: Sensor):
    sensors_table.insert_one(newSensor.dict())
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=newSensor.dict())


PATH_STORE_SENIOR = '/store-senior/'


@app.post(PATH_STORE_SENIOR)
def store_senior(newSenior: Senior):
    d = newSenior.dict()
    d["enabled"] = False
    if "sensorId" in d:
        d.pop("sensorId")
    seniors_table.insert_one(d)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=newSenior.dict())


PATH_ASSIGN_SENSOR_TO_SENIOR = "/assign-sensor"


# TODO think carefully race-conditions here
#   eg. user1 assigning sensors, while user2 changes tables: would mess _raise_...
@app.post(PATH_ASSIGN_SENSOR_TO_SENIOR)
def assign_sensor(sensorId: int, seniorId: int):
    _raise_if_senior_doesnt_exist(seniorId=seniorId)
    _raise_if_sensor_already_assigned(sensorId=sensorId)
    _raise_if_sensor_doesnt_exist(sensorId=sensorId)
    seniors_table.find_one_and_update({"seniorId": seniorId}, {"$set": {"sensorId": sensorId}})
    return {f"Sensor {sensorId} assigned to senior {seniorId}."}


def _raise_if_sensor_already_assigned(sensorId):
    if seniors_table.find_one({"sensorId": sensorId}):
        _raise_http_422(msg=f"Sensor {sensorId} already belongs to a senior. Please try another sensor.")


def _raise_if_senior_doesnt_exist(seniorId):
    if not seniors_table.find_one({"seniorId": seniorId}):
        _raise_http_422(msg=f"Senior {seniorId} doesn't exist. Please register him first, then assign a sensor.")


def _raise_if_sensor_defined_for_unregistered_senior(senior_id):
    if seniors_table.find_one({"seniorId": senior_id}):
        _raise_http_422(msg="Defining sensor ID upon senior creation is forbidden.")


def _raise_if_sensor_doesnt_exist(sensorId):
    if not sensors_table.find_one({"sensorId": sensorId}):
        _raise_http_422(msg=f"Sensor ID {sensorId} doesn't exist.")


@app.get("/senior/{seniorId}")
def get_senior(seniorId: int):
    if not seniors_table.find_one({"seniorId": seniorId}):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Senior {seniorId} doesn't exist. Please register him first.")
    d = seniors_table.find_one({"seniorId": seniorId})
    d.pop('_id')
    return d


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

    # Or run: $ uvicorn app.main:app --reload
    #   and connect to http://127.0.0.1:8000/docs#/
