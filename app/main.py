from datetime import datetime, timedelta

import jwt
import pymongo as pymongo
from fastapi import FastAPI, HTTPException, Request
from pydantic.types import conint
from pydantic.validators import Literal
from starlette.responses import JSONResponse, Response
from pydantic import BaseModel
from typing import Optional
from starlette import status
import uvicorn
from app.secret_handler import PASS_MONGO_DB_USER0, API_KEY_VALUE_PAIR, JWT_PRIVATE_KEY
from configuration import APIKEY_MIDDLEWARE_ACTIVE, JWT_MIDDLEWARE_ACTIVE, JWT_USER_NAME, JWT_TOKEN_DURATION_HOURS, \
    JWT_ALGORITHM

API_KEY, API_VALUE = list(API_KEY_VALUE_PAIR.items())[0]


def _raise_http_422(msg):
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)


client = pymongo.MongoClient(
    f"mongodb+srv://user0:{PASS_MONGO_DB_USER0}@cluster0.4derf.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client["test"]

homes_table = db['homes']
sensors_table = db['sensors']
seniors_table = db['seniors']

ALLOWED_HOME_TYPES = ("NURSING", "PRIVATE")

MONGODB_INT_UPPER_LIM = 2 ** 31
ConstrainedIntMongo = conint(gt=0, lt=MONGODB_INT_UPPER_LIM)


class Home(BaseModel):
    homeId: ConstrainedIntMongo
    name: str
    type: Literal[ALLOWED_HOME_TYPES]


class Sensor(BaseModel):
    sensorId: ConstrainedIntMongo
    hardwareVersion: str
    softwareVersion: str


# TODO "Senior" -> "Patient"; "senior"/"sensor" too similar + hard to read; keep seniorId for clients as is
class Senior(BaseModel):
    seniorId: ConstrainedIntMongo
    name: str
    homeId: ConstrainedIntMongo
    enabled: bool
    sensorId: Optional[int] = 0


class SensorAssignment(BaseModel):
    seniorId: ConstrainedIntMongo
    sensorId: ConstrainedIntMongo


app = FastAPI()

PATH_STORE_HOME = '/store-home'
PATH_STORE_SENSOR = '/store-sensor'
PATH_STORE_SENIOR = '/store-senior'
PATH_ASSIGN_SENSOR_TO_SENIOR = "/assign-sensor"
PATH_GET_SENIOR = "/get-senior"
PATH_GET_JWT = "/create-jwt"


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
    d.pop("_id")
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=d)


async def _raise_if_home_doesnt_exist(homeId):
    if not homes_table.find_one({"homeId": homeId}):
        _raise_http_422(
            msg=f"Can't assign senior to home ID {homeId} (home doesn't exist).")


# TODO think carefully race-conditions here
#   eg. user1 assigning sensors, while user2 changes tables: would mess _raise_...
@app.put(PATH_ASSIGN_SENSOR_TO_SENIOR)
async def assign_sensor(sensorAssignment: SensorAssignment):
    d = sensorAssignment.dict()
    sensorId = d["sensorId"]
    seniorId = d["seniorId"]
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


@app.get(PATH_GET_JWT)
async def create_jwt():
    # eg. headers = {"X-Token": "foo"} ?
    return JSONResponse(status_code=status.HTTP_201_CREATED, headers={"token": signed_jwt_token()})


def signed_jwt_token(duration_h=JWT_TOKEN_DURATION_HOURS):
    expiration = datetime.utcnow() + timedelta(hours=duration_h)
    d = {"username": JWT_USER_NAME, "exp": expiration}
    # (function output tested here: https://jwt.io/ ; displays local time)
    return jwt.encode(payload=d, key=JWT_PRIVATE_KEY, algorithm=JWT_ALGORITHM)


PATHS_PROTECTED_WITH_API_KEY = {PATH_STORE_HOME,
                                PATH_STORE_SENSOR,
                                PATH_STORE_SENIOR,
                                PATH_ASSIGN_SENSOR_TO_SENIOR,
                                PATH_GET_SENIOR
                                }

PATHS_PROTECTED_WITH_JWT = {PATH_STORE_HOME,
                            PATH_STORE_SENSOR,
                            PATH_STORE_SENIOR,
                            PATH_ASSIGN_SENSOR_TO_SENIOR,
                            PATH_GET_SENIOR}


@app.middleware("http")
async def middleware_header_api_key(req: Request, call_next):
    if not APIKEY_MIDDLEWARE_ACTIVE:
        return await call_next(req)

    if not protected_path(req, paths_protected=PATHS_PROTECTED_WITH_API_KEY):
        return await call_next(req)

    try:
        if req.headers[API_KEY] == API_VALUE:
            response = await call_next(req)
            return response
    except KeyError:
        pass

    return Response(status_code=401, content="Api-key in headers missing or incorrect.")


@app.middleware("http")
async def middleware_jwt(req: Request, call_next):
    if not JWT_MIDDLEWARE_ACTIVE:
        return await call_next(req)

    if not protected_path(req, paths_protected=PATHS_PROTECTED_WITH_JWT):
        return await call_next(req)

    headers = req.headers
    if "token" not in headers:
        return Response(status_code=401, content="No 'token' key in headers.")

    token = headers["token"]
    try:
        decoded_token = jwt.decode(token, key=JWT_PRIVATE_KEY, algorithms=JWT_ALGORITHM)
        if token_user_correct(t=decoded_token):
            return await call_next(req)
    except jwt.PyJWTError:
        pass
    return Response(status_code=401, content='Token failed.')


def endpoint_path_matches(endpoint_path, req):
    requested_path = str(req.url)
    p = str(req.base_url).rstrip('/') + endpoint_path
    return requested_path.startswith(p)


def protected_path(req, paths_protected):
    for p in paths_protected:
        if endpoint_path_matches(p, req=req):
            return True
    return False


def token_user_correct(t):
    return t["username"] == JWT_USER_NAME


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

    # Or run: $ uvicorn app.main:app --reload
    #   and connect to http://127.0.0.1:8000/docs#/
