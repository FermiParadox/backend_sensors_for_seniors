from unittest import TestCase
from fastapi.testclient import TestClient

from app.main import app


class Test_store_home(TestCase):
    def setUp(self) -> None:
        from app.main import PATH_STORE_HOME, ALLOWED_HOME_TYPES
        self.PATH_STORE_HOME = PATH_STORE_HOME
        self.ALLOWED_HOME_TYPES = ALLOWED_HOME_TYPES

    def test_store_home_type_incorrect(self):
        client = TestClient(app)
        response = client.post(self.PATH_STORE_HOME,
                               json={"homeId": 1, "name": 'Clinic XY',
                                     "type": "Hospital"})
        response_code = response.status_code
        self.assertEqual(response_code, 403)

    def test_store_home_status200(self):
        client = TestClient(app)
        for home_type in self.ALLOWED_HOME_TYPES:
            response = client.post(self.PATH_STORE_HOME,
                                   json={"homeId": 1, "name": 'Clinic XY',
                                         "type": home_type})
            response_code = response.status_code
            self.assertEqual(response_code, 200, msg=str(response.json()))



# TODO test token of Part II (if implemented):
# response = client.get("/items/foo", headers={"X-Token": "coneofsilence"})
