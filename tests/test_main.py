from copy import deepcopy
from unittest import TestCase
from fastapi.testclient import TestClient

from app.main import app, homes_table


class Test_store_home(TestCase):
    def setUp(self) -> None:
        # (avoiding global import to prevent accidental bugs due to names' similarity)
        from app.main import PATH_STORE_HOME, ALLOWED_HOME_TYPES
        self.PATH_STORE_HOME = PATH_STORE_HOME
        self.ALLOWED_HOME_TYPES = ALLOWED_HOME_TYPES
        self.home_id_test_name = 'skljtioutioq-_wtaklsjklasd asd'
        self.valid_home = {"homeId": 23897523,
                           "name": self.home_id_test_name,
                           "type": list(self.ALLOWED_HOME_TYPES)[0]}
        self.client = TestClient(app)

    def tearDown(self) -> None:
        homes_table.delete_many({"homeId": self.home_id_test_name})

    def valid_home_deepcopy(self):
        return deepcopy(self.valid_home)

    def _response(self, data):
        return self.client.post(self.PATH_STORE_HOME, json=data)

    def assert_response_code_is_x(self, data, x):
        response = self._response(data)
        self.assertEqual(response.status_code, x, msg=str(response.json()))

    def test_invalid_home_id_0(self):
        d = deepcopy(self.valid_home)
        d["homeId"] = 0
        self.assert_response_code_is_x(data=d, x=422)

    def test_invalid_home_id_negative(self):
        d = self.valid_home_deepcopy()
        d["homeId"] = -4
        self.assert_response_code_is_x(data=d, x=422)

    def test_type_incorrect(self):
        d = self.valid_home_deepcopy()
        d["type"] = "SomeInvalidType"
        self.assert_response_code_is_x(data=d, x=422)

    def test_not_enough_args(self):
        for key in self.valid_home.keys():
            d = self.valid_home_deepcopy()
            d.pop(key)
            self.assert_response_code_is_x(data=d, x=422)

    def test_successful(self):
        d = self.valid_home_deepcopy()
        for home_type in self.ALLOWED_HOME_TYPES:
            d["type"] = home_type
            self.assert_response_code_is_x(data=d, x=201)


class Test_store_senior(TestCase):
    def setUp(self) -> None:
        from app.main import PATH_STORE_SENIOR
        self.PATH_STORE_SENIOR = PATH_STORE_SENIOR
        self.valid_senior = {'seniorId': 111,
                             'name': 'Smith',
                             'homeId': 1,
                             'enabled': False,
                             'sensorId': 0}

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
