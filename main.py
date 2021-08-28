from fastapi import FastAPI, Path
from pydantic import BaseModel, validator
from typing import Optional
import uvicorn

homes_table = {
}
HOME_ID_BOUNDS_INCLUSIVE = 1, 10 ** 6
HOME_ID_MIN_INC, HOME_ID_MAX_INC = HOME_ID_BOUNDS_INCLUSIVE

sensors_table = {
}

seniors_table = {
}


class Home(BaseModel):
    homeId: int
    name: str
    type: str

    @validator("type")
    def types_allowed(cls, v):
        if v != "NURSING" and v != "PRIVATE":
            raise ValueError('Home type can be either "NURSING" or "PRIVATE".')
        return v


class Sensor(BaseModel):
    sensorId: int
    hardwareVersion: str
    softwareVersion: str


class Senior(BaseModel):
    seniorId: int
    name: str
    homeId: int
    enabled: bool = False
    sensorId: Optional[int]


app = FastAPI()


# TODO: consider removal (ask clarification); perhaps they want no GET to exist
@app.get("/homes")
def homes():
    return homes_table


# TODO: consider removal (ask clarification); perhaps they want no GET to exist
@app.get("/homes/{homeId}")
def get_home(homeId: int = Path(None, description="The ID of the nursing/private home.",
                                ge=HOME_ID_MIN_INC, lt=HOME_ID_MAX_INC)):
    if homeId not in homes_table:
        return {"Home ID not found."}
    return homes_table[homeId]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
