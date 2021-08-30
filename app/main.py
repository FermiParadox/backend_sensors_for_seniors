from fastapi import FastAPI, Path, HTTPException
from pydantic import BaseModel, validator, PositiveInt
from typing import Optional
from starlette import status
import uvicorn


def raise_http_403(msg):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)


homes_table = {}

sensors_table = {}

seniors_table = {}

ALLOWED_HOME_TYPES = {"NURSING", "PRIVATE"}


def _is_allowed_home_type(home_type):
    return home_type in ALLOWED_HOME_TYPES


class Home(BaseModel):
    homeId: PositiveInt
    name: str
    type: str

    @validator("type")
    def type_allowed(cls, home_type):
        if not _is_allowed_home_type(home_type=home_type):
            raise_http_403(msg=f"Home type can be either NURSING or PRIVATE ('{home_type}' not allowed).")
        return home_type


class Sensor(BaseModel):
    sensorId: PositiveInt
    hardwareVersion: str
    softwareVersion: str


# TODO "Senior" -> "Patient"; "senior"/"sensor" too similar + hard to read; keep seniorId for clients as is
class Senior(BaseModel):
    seniorId: PositiveInt
    name: str
    homeId: PositiveInt
    enabled: bool = False
    sensorId: Optional[int] = 0

    @validator("homeId")
    def home_exists(cls, homeId):
        if homeId not in homes_table:
            raise_http_403(msg=f"Can't assign senior to home ID {homeId} (home doesn't exist). Please try another one.")
        return homeId


app = FastAPI()


# TODO: consider removal (ask clarification); perhaps they want no GET to exist
@app.get("/homes")
def homes():
    return homes_table


# TODO: consider removal (ask clarification); perhaps they want no GET to exist
@app.get("/seniors")
def seniors():
    return seniors_table


# TODO: consider removal (ask clarification); perhaps they want no GET to exist
@app.get("/sensors")
def seniors():
    return sensors_table


# TODO: consider removal (ask clarification); perhaps they want no GET to exist
@app.get("/homes/{homeId}")
def get_home(homeId=Path(None, description="The ID of the nursing/private home.")):
    if homeId not in homes_table:
        return {"Home ID not found."}
    return homes_table[homeId]


PATH_STORE_HOME = '/store-home/'


# TODO: consider removal (ask clarification); perhaps they want no GET to exist
@app.post(PATH_STORE_HOME)
def store_home(newHome: Home):
    home_id = newHome.homeId
    homes_table.update({home_id: newHome})
    return {"Home successfully added."}


PATH_STORE_SENSOR = '/store-sensor/'


@app.post(PATH_STORE_SENSOR)
def store_sensor(newSensor: Sensor):
    sensor_id = newSensor.sensorId
    sensors_table.update({sensor_id: newSensor})
    return {"Sensor successfully added."}


def _raise_if_sensor_defined_for_new_senior(sensor_id, senior_id):
    if sensor_id:
        # Check new senior
        if senior_id not in seniors_table:
            raise_http_403(msg="Defining sensor ID upon senior creation is forbidden.")
    return sensor_id


PATH_STORE_SENIOR = '/store-senior/'


@app.post(PATH_STORE_SENIOR)
def store_senior(new_senior: Senior):
    _raise_if_sensor_defined_for_new_senior(sensor_id=new_senior.sensorId, senior_id=new_senior.seniorId)
    senior_id = new_senior.seniorId
    seniors_table.update({senior_id: new_senior})
    return {"Senior successfully added."}


PATH_ASSIGN_SENSOR_TO_SENIOR = "/assign-sensor"


@app.post(PATH_ASSIGN_SENSOR_TO_SENIOR)
def assign_sensor(sensorId: int, seniorId: int):
    # TODO: check better searching way in mongoDB, AFTER adding mongoDB
    if seniorId not in seniors_table:
        raise_http_403(msg=f"Senior {seniorId} doesn't exist. Please register him first, then assign a sensor.")
    sensors_used = {senior.sensorId for senior in seniors_table.values() if senior.sensorId}
    if sensorId in sensors_used:
        raise_http_403(msg=f"Sensor {sensorId} already belongs to a senior. Please try another one.")
    seniors_table[seniorId].sensorId = sensorId
    return {f"Sensor {sensorId} successfully assigned to senior {seniorId}."}


@app.get("/senior/{seniorId}")
def get_senior(seniorId: int):
    if seniorId not in seniors_table:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Senior {seniorId} doesn't exist. Please register him first, then assign a sensor.")
    return seniors_table[seniorId]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
