import pymongo as pymongo
from fastapi import FastAPI, HTTPException, Request
from pydantic.validators import Literal
from starlette.responses import JSONResponse, Response
from pydantic import BaseModel, PositiveInt
from typing import Optional
from starlette import status
import uvicorn
from app.secret_handler import PASS_MONGO_DB_USER0, KEY_VALUE_PAIR_PART2


def _raise_http_422(msg):
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)


client = pymongo.MongoClient(
    f"mongodb+srv://user0:{PASS_MONGO_DB_USER0}@cluster0.4derf.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client["test"]

homes_table = db['homes']
sensors_table = db['sensors']
seniors_table = db['seniors']

ALLOWED_HOME_TYPES = ("NURSING", "PRIVATE")


class Home(BaseModel):
    homeId: PositiveInt
    name: str
    type: Literal[ALLOWED_HOME_TYPES]


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


app = FastAPI()

PATH_STORE_HOME = '/store-home'
PATH_STORE_SENSOR = '/store-sensor'
PATH_STORE_SENIOR = '/store-senior'
PATH_ASSIGN_SENSOR_TO_SENIOR = "/assign-sensor"
PATH_GET_SENIOR = "/get-senior"
PATH_GET_JWT_COOKIE = "/get-jwt-cookie"


@app.post(PATH_STORE_HOME)
async def store_home(newHome: Home):
    homes_table.insert_one(newHome.dict())
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=newHome.dict())


@app.post(PATH_STORE_SENSOR)
async def store_sensor(newSensor: Sensor):
    sensors_table.insert_one(newSensor.dict())
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=newSensor.dict())


@app.post(PATH_STORE_SENIOR)
async def store_senior(newSenior: Senior):
    d = newSenior.dict()
    await _raise_if_home_doesnt_exist(homeId=d["homeId"])
    # Ignore "enabled" and "sensorId"
    d["enabled"] = False
    if "sensorId" in d:
        d.pop("sensorId")
    seniors_table.insert_one(d)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=newSenior.dict())


async def _raise_if_home_doesnt_exist(homeId):
    if not homes_table.find_one({"homeId": homeId}):
        _raise_http_422(
            msg=f"Can't assign senior to home ID {homeId} (home doesn't exist).")


# TODO think carefully race-conditions here
#   eg. user1 assigning sensors, while user2 changes tables: would mess _raise_...
@app.put(PATH_ASSIGN_SENSOR_TO_SENIOR)
async def assign_sensor(sensorId: int, seniorId: int):
    await _raise_if_senior_doesnt_exist(seniorId=seniorId)
    await _raise_if_sensor_already_assigned(sensorId=sensorId)
    await _raise_if_sensor_doesnt_exist(sensorId=sensorId)
    seniors_table.find_one_and_update({"seniorId": seniorId}, {"$set": {"sensorId": sensorId}})
    return {f"Sensor {sensorId} assigned to senior {seniorId}."}


async def _raise_if_sensor_already_assigned(sensorId):
    if seniors_table.find_one({"sensorId": sensorId}):
        _raise_http_422(msg=f"Sensor {sensorId} already belongs to a senior.")


async def _raise_if_senior_doesnt_exist(seniorId):
    if not seniors_table.find_one({"seniorId": seniorId}):
        _raise_http_422(msg=f"Senior {seniorId} doesn't exist. Please register him first, then assign a sensor.")


async def _raise_if_sensor_doesnt_exist(sensorId):
    if not sensors_table.find_one({"sensorId": sensorId}):
        _raise_http_422(msg=f"Sensor ID {sensorId} doesn't exist.")


@app.get(PATH_GET_SENIOR)
async def get_senior(seniorId: int):
    if not seniors_table.find_one({"seniorId": seniorId}):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Senior {seniorId} doesn't exist.")
    match = seniors_table.find_one({"seniorId": seniorId})
    match.pop('_id')
    return match


@app.get(PATH_GET_JWT_COOKIE)
async def get_jwt_cookie():
    return JSONResponse(status_code=status.HTTP_201_CREATED, content="Cookie created.")


@app.middleware("http")
async def middleware_header_api_key(req: Request, call_next):
    try:
        if req.headers[KEY_VALUE_PAIR_PART2[0]] == KEY_VALUE_PAIR_PART2[1]:
            response = await call_next(req)
            return response
    except KeyError:
        pass

    return Response(status_code=401)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

    # Or run: $ uvicorn app.main:app --reload
    #   and connect to http://127.0.0.1:8000/docs#/
