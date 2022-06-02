from datetime import datetime, timedelta
from enum import Enum
from typing import Iterable, Dict
from fastapi import FastAPI, HTTPException, Request
from starlette.datastructures import Headers
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_201_CREATED, HTTP_404_NOT_FOUND
import uvicorn
import jwt

from app.model.home import homes_table, Home
from app.model.senior import seniors_table, Senior
from app.model.sensor import sensors_table, Sensor
from app.model.sensor_assignment import SensorAssignment
from app.secret_handler import API_KEY_VALUE_PAIR, JWT_PRIVATE_KEY
from configuration import APIKEY_MIDDLEWARE_ACTIVE, JWT_MIDDLEWARE_ACTIVE, JWT_USER_NAME, JWT_DURATION_HOURS, \
    JWT_ALGORITHM

API_KEY, API_VALUE = list(API_KEY_VALUE_PAIR.items())[0]


def _raise_http_422(msg):
    raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)


class EndpointPath(str, Enum):
    store_home = '/store-home'
    store_sensor = '/store-sensor'
    store_senior = '/store-senior'
    assign_sensor = "/assign-sensor"
    get_senior = "/get-senior"
    get_jwt = "/create-jwt"


app = FastAPI()


@app.post(EndpointPath.store_home)
async def store_home(newHome: Home):
    homes_table.insert_one(newHome.dict())
    return JSONResponse(status_code=HTTP_201_CREATED, content=newHome.dict())


@app.post(EndpointPath.store_sensor)
async def store_sensor(newSensor: Sensor):
    sensors_table.insert_one(newSensor.dict())
    return JSONResponse(status_code=HTTP_201_CREATED, content=newSensor.dict())


@app.post(EndpointPath.store_senior)
async def store_senior(newSenior: Senior):
    d = newSenior.dict()
    await _raise_if_home_doesnt_exist(homeId=d["homeId"])
    # Ignore "enabled" and "sensorId"
    d["enabled"] = False
    if "sensorId" in d:
        d.pop("sensorId")
    seniors_table.insert_one(d)
    d.pop("_id")
    return JSONResponse(status_code=HTTP_201_CREATED, content=d)


async def _raise_if_home_doesnt_exist(homeId) -> None:
    if not homes_table.find_one({"homeId": homeId}):
        _raise_http_422(msg=f"Can't assign senior to home ID {homeId} (home doesn't exist).")


# TODO mongo server-side (race conditions + delay)
@app.put(EndpointPath.assign_sensor)
async def assign_sensor(sensorAssignment: SensorAssignment):
    d = sensorAssignment.dict()
    sensorId = d["sensorId"]
    seniorId = d["seniorId"]
    await _raise_senior_doesnt_exist(seniorId=seniorId)
    await _raise_sensor_already_assigned(sensorId=sensorId)
    await _raise_sensor_doesnt_exist(sensorId=sensorId)
    seniors_table.find_one_and_update({"seniorId": seniorId},
                                      {"$set": {
                                          "sensorId": sensorId}})
    return {f"Sensor {sensorId} assigned to senior {seniorId}."}


async def _raise_sensor_already_assigned(sensorId) -> None:
    if seniors_table.find_one({"sensorId": sensorId}):
        _raise_http_422(msg=f"Sensor {sensorId} already belongs to a senior.")


async def _raise_senior_doesnt_exist(seniorId) -> None:
    if not seniors_table.find_one({"seniorId": seniorId}):
        _raise_http_422(msg=f"Senior {seniorId} doesn't exist. Please register him first, then assign a sensor.")


async def _raise_sensor_doesnt_exist(sensorId) -> None:
    if not sensors_table.find_one({"sensorId": sensorId}):
        _raise_http_422(msg=f"Sensor ID {sensorId} doesn't exist.")


@app.get(EndpointPath.get_senior)
async def get_senior(seniorId: int):
    if not seniors_table.find_one({"seniorId": seniorId}):
        raise HTTPException(status_code=HTTP_404_NOT_FOUND,
                            detail=f"Senior {seniorId} doesn't exist.")
    match = seniors_table.find_one({"seniorId": seniorId})
    match.pop('_id')
    return match


@app.get(EndpointPath.get_jwt)
async def create_jwt():
    return JSONResponse(status_code=HTTP_201_CREATED, headers={"token": signed_jwt_token()})


def signed_jwt_token(duration_h: float = JWT_DURATION_HOURS) -> str:
    expiration = datetime.utcnow() + timedelta(hours=duration_h)
    d = {"username": JWT_USER_NAME, "exp": expiration}
    # (function output can be tested here: https://jwt.io/ ; displays local time)
    return jwt.encode(payload=d, key=JWT_PRIVATE_KEY, algorithm=JWT_ALGORITHM)


PATHS_PROTECTED_WITH_JWT = {EndpointPath.store_home,
                            EndpointPath.store_senior,
                            EndpointPath.store_sensor,
                            EndpointPath.assign_sensor,
                            EndpointPath.get_senior}


@app.middleware("http")
async def middleware_header_api_key(req: Request, call_next):
    if not APIKEY_MIDDLEWARE_ACTIVE:
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

    if not is_protected_path(req, paths_protected=PATHS_PROTECTED_WITH_JWT):
        return await call_next(req)

    headers = req.headers
    if token_header_exists(headers=headers):
        return Response(status_code=401, content="No 'token' key in headers.")

    token = headers["token"]
    try:
        decoded_token = jwt.decode(token, key=JWT_PRIVATE_KEY, algorithms=JWT_ALGORITHM)
        if token_user_correct(token=decoded_token):
            return await call_next(req)
    except jwt.PyJWTError:
        pass
    return Response(status_code=401, content='Token failed.')


def token_header_exists(headers: Headers) -> bool:
    return "token" not in headers


def is_protected_path(req: Request, paths_protected: Iterable) -> bool:
    for p in paths_protected:
        if endpoint_path_matches(p, req=req):
            return True
    return False


def endpoint_path_matches(endpoint_path: EndpointPath, req: Request) -> bool:
    """Compare requested path with stored endpoint path.

    If this is matched:
    > http://127.0.0.1:8000/get-senior

    then this is matched as well:
    http://127.0.0.1:8000/get-senior?seniorId=5
    """
    requested_path = str(req.url)
    p = str(req.base_url).rstrip('/') + endpoint_path
    return requested_path.startswith(p)


def token_user_correct(token: Dict[str]) -> bool:
    return token["username"] == JWT_USER_NAME


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

    # Or run: $ uvicorn app.main:app --reload
    #   and connect to http://127.0.0.1:8000/docs#/
