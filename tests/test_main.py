from unittest import TestCase
from fastapi.testclient import TestClient

from app.main import app


class Test_store_home(TestCase):
    def setUp(self) -> None:
        # (avoiding global import to prevent accidental bugs due to names' similarity)
        from app.main import PATH_STORE_HOME, ALLOWED_HOME_TYPES
        self.PATH_STORE_HOME = PATH_STORE_HOME
        self.ALLOWED_HOME_TYPES = ALLOWED_HOME_TYPES

    def test_store_home_type_incorrect(self):
        client = TestClient(app)
        response = client.post(self.PATH_STORE_HOME,
                               json={"homeId": 1, "name": 'Clinic XY',
                                     "type": "Hospital"})
        response_code = response.status_code
        self.assertEqual(response_code, 422, msg=str(response.json()))

    def test_store_home_successful(self):
        client = TestClient(app)
        for home_type in self.ALLOWED_HOME_TYPES:
            response = client.post(self.PATH_STORE_HOME,
                                   json={"homeId": 1, "name": 'Clinic XY',
                                         "type": home_type})
            response_code = response.status_code
            self.assertEqual(response_code, 201, msg=str(response.json()))


class Test_store_senior(TestCase):
    def setUp(self) -> None:
        from app.main import PATH_STORE_SENIOR
        self.PATH_STORE_SENIOR = PATH_STORE_SENIOR

    # TODO create database entries before testing; following works only when home1 is created (in previous test class)
    #   remove entries after testing. Or keep them indefinitely for testing purposes.
    def test_store_senior_successful(self):
        client = TestClient(app)
        response = client.post(self.PATH_STORE_SENIOR,
                               json={'seniorId': 111,
                                     'name': 'Smith',
                                     'homeId': 1,
                                     'enabled': False,
                                     'sensorId': 0})
        response_code = response.status_code
        self.assertEqual(response_code, 201, msg=str(response.json()))

    def test_store_senior_at_non_existing_home(self):
        client = TestClient(app)
        response = client.post(self.PATH_STORE_SENIOR,
                               json={'seniorId': 111,
                                     'name': 'Smith',
                                     'homeId': 2,
                                     'enabled': False,
                                     'sensorId': 0})
        response_code = response.status_code
        self.assertEqual(response_code, 422, msg=str(response.json()))


# TODO test token of Part II (if implemented):
#   response = client.get("/items/foo", headers={"X-Token": "foo"})
#   (tutorial at https://fastapi.tiangolo.com/tutorial/testing/)
