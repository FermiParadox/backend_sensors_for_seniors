from abc import ABC, abstractmethod
from copy import deepcopy
from json import JSONDecodeError
from unittest import TestCase
from fastapi.testclient import TestClient

from app.model.home import HomeTypes
from app.secret_handler import API_KEY_VALUE_PAIR
from app.main import app, homes_table, sensors_table, seniors_table, EndpointPaths

_DELETION_MARKER_STRING = 'test marker string used for deleting test-entries'

TOKEN_HEADER = {'token': 'to-be-replaced'}
final_extra_header = {}
final_extra_header.update(TOKEN_HEADER)
final_extra_header.update(API_KEY_VALUE_PAIR)


class TestEntriesDeletionInDB(ABC):
    """Ensure database is not accidentally filled with test entries."""

    @property
    @abstractmethod
    def collection_name(self):
        pass

    def delete_test_objects_in_db(self, key):
        self.collection_name.delete_many({key: _DELETION_MARKER_STRING})

    @property
    @abstractmethod
    def key_with_deletion_marker_value(self):
        """
        This key contains the deletion value marker in the database documents.
        On test-class tear-down all entries containing this key-name
        and the deletion-marker as a value, are deleted from the database.

        WARNING: Make sure the selected key is not optional, otherwise some entries might not be deleted,
        due to how other methods work.
        """
        return ""

    def tearDown(self) -> None:
        self.delete_test_objects_in_db(key=self.key_with_deletion_marker_value)


def new_token():
    r = TestClient(app).get(url=EndpointPaths.get_jwt, json={}, headers=final_extra_header)
    return r.headers['token']


final_extra_header['token'] = new_token()


def post_response(data, client: TestClient, path, headers=None):
    if headers is None:
        headers = final_extra_header
    return client.post(url=path, json=data, headers=headers)


def put_response(data, client: TestClient, path, headers=None):
    if headers is None:
        headers = final_extra_header
    return client.put(url=path, json=data, headers=headers)


def get_response(data, client: TestClient, path, headers=None):
    if headers is None:
        headers = final_extra_header
    return client.get(url=path, json=data, headers=headers)


def response_(r_type):
    if r_type == 'post':
        r = post_response
    elif r_type == 'put':
        r = put_response
    elif r_type == 'get':
        r = get_response
    else:
        raise NotImplementedError
    return r


class TestCaseWithDeletion(TestEntriesDeletionInDB, TestCase):
    """Implements methods used in most request-tests."""

    def _assert_response_code_is_x(self, data, x: int, client, path, r_type, headers=None):
        resp_func = response_(r_type=r_type)
        resp = resp_func(data=data, client=client, path=path, headers=headers)
        try:
            msg = resp.json()
        except JSONDecodeError:
            msg = ''
        self.assertEqual(x, resp.status_code, msg=msg)

    @abstractmethod
    def assert_response_code_is_x(self, data, x):
        pass

    @abstractmethod
    def valid_body_deepcopy(self):
        pass

    # SIDE-NOTE: Can't use @abstractmethod test_foo after _test_foo as before
    # because it probably conflicts with how TestCase is implemented 
    # (methods starting with "test.." are run) and raises:
    # > TypeError: Can't instantiate abstract class TestCaseWithDeletion with abstract methods assert_response_code_is_x
    def _test_not_enough_args(self, valid_body):
        for key in valid_body.keys():
            if key == self.key_with_deletion_marker_value:
                continue
            d = self.valid_body_deepcopy()
            d.pop(key)
            self.assert_response_code_is_x(data=d, x=422)


class TestStoreHome(TestCaseWithDeletion):
    @property
    def collection_name(self):
        return homes_table

    @property
    def key_with_deletion_marker_value(self):
        return "name"

    def setUp(self) -> None:
        # (avoiding global import to prevent accidental bugs due to names' similarity)
        self.PATH_STORE_HOME = EndpointPaths.store_home
        self.valid_home = {"homeId": 23897523,
                           self.key_with_deletion_marker_value: _DELETION_MARKER_STRING,
                           "type": HomeTypes.nursing}
        self.client = TestClient(app)

    def valid_body_deepcopy(self):
        return deepcopy(self.valid_home)

    def assert_response_code_is_x(self, data, x):
        return self._assert_response_code_is_x(data, x, client=self.client, path=self.PATH_STORE_HOME, r_type='post')

    def test_successful(self):
        d = self.valid_body_deepcopy()
        d["type"] = HomeTypes.nursing
        self.assert_response_code_is_x(data=d, x=201)
        d["type"] = HomeTypes.private
        self.assert_response_code_is_x(data=d, x=201)

    def test_invalid_home_id_0(self):
        d = self.valid_body_deepcopy()
        d["homeId"] = 0
        self.assert_response_code_is_x(data=d, x=422)

    def test_invalid_home_id_negative(self):
        d = self.valid_body_deepcopy()
        d["homeId"] = -4
        self.assert_response_code_is_x(data=d, x=422)

    def test_type_incorrect(self):
        d = self.valid_body_deepcopy()
        d["type"] = "SomeInvalidType"
        self.assert_response_code_is_x(data=d, x=422)

    def test_not_enough_args(self):
        self._test_not_enough_args(valid_body=self.valid_home)

    def test_no_token(self):
        self._assert_response_code_is_x(data=self.valid_body_deepcopy(), x=401,
                                        client=self.client, path=self.PATH_STORE_HOME, r_type='post',
                                        headers=API_KEY_VALUE_PAIR)

    def test_no_apikey(self):
        self._assert_response_code_is_x(data=self.valid_body_deepcopy(), x=401,
                                        client=self.client, path=self.PATH_STORE_HOME, r_type='post',
                                        headers=TOKEN_HEADER)


class TestStoreSensor(TestCaseWithDeletion):
    VALID_SENSOR_EXAMPLE = {
        'sensorId': 236236236,
        "hardwareVersion": _DELETION_MARKER_STRING,
        "softwareVersion": "1.5.15c"}

    @property
    def collection_name(self):
        return sensors_table

    @property
    def key_with_deletion_marker_value(self):
        return "hardwareVersion"

    def setUp(self) -> None:
        self.PATH_STORE_SENSOR = EndpointPaths.store_sensor
        self.client = TestClient(app)
        self.valid_body = self.VALID_SENSOR_EXAMPLE
        self.valid_body.update({self.key_with_deletion_marker_value: _DELETION_MARKER_STRING})

    def assert_response_code_is_x(self, data, x):
        return self._assert_response_code_is_x(data, x, client=self.client, path=self.PATH_STORE_SENSOR, r_type='post')

    def valid_body_deepcopy(self):
        return deepcopy(self.valid_body)

    def test_successful(self):
        self.assert_response_code_is_x(data=self.valid_body, x=201)

    def test_not_enough_args(self):
        self._test_not_enough_args(valid_body=self.valid_body)

    def test_no_token(self):
        self._assert_response_code_is_x(data=self.valid_body_deepcopy(), x=401,
                                        client=self.client, path=self.PATH_STORE_SENSOR, r_type='post',
                                        headers=API_KEY_VALUE_PAIR)

    def test_no_apikey(self):
        self._assert_response_code_is_x(data=self.valid_body_deepcopy(), x=401,
                                        client=self.client, path=self.PATH_STORE_SENSOR, r_type='post',
                                        headers=TOKEN_HEADER)


class TestStoreSenior(TestCaseWithDeletion):
    VALID_SENIOR_EXAMPLE = {'seniorId': 999879795,
                            "name": _DELETION_MARKER_STRING,
                            'homeId': 1,
                            'enabled': False}

    @property
    def collection_name(self):
        return seniors_table

    @property
    def key_with_deletion_marker_value(self):
        return "name"

    def setUp(self) -> None:
        self.PATH_STORE_SENIOR = EndpointPaths.store_senior
        self.client = TestClient(app)
        self.valid_senior = self.VALID_SENIOR_EXAMPLE
        self.valid_senior.update({self.key_with_deletion_marker_value: _DELETION_MARKER_STRING})

    def assert_response_code_is_x(self, data, x):
        return self._assert_response_code_is_x(data, x, client=self.client, path=self.PATH_STORE_SENIOR, r_type='post')

    def valid_body_deepcopy(self):
        return deepcopy(self.valid_senior)

    def test_successful(self):
        self.assert_response_code_is_x(data=self.valid_senior, x=201)

    def test_store_at_non_existing_home(self):
        d = self.valid_body_deepcopy()
        # I assume this value will never actually exist in the DB.
        # If it does, this test will falsely fail
        d["homeId"] = 999999999
        self.assert_response_code_is_x(data=d, x=422)

    def test_sensor_id_ignored(self):
        d = self.valid_body_deepcopy()
        d.update({'sensorId': 5})
        self.assert_response_code_is_x(data=d, x=201)
        d.pop("sensorId")
        match = seniors_table.find_one(d)
        self.assertRaises(KeyError, lambda: match["sensorId"])

    # prone to error; when everything is locked with 401 this incorrectly passes
    def test_enabled_is_false_by_default(self):
        d = self.valid_body_deepcopy()
        d["enabled"] = True
        post_response(data=d, client=self.client, path=self.PATH_STORE_SENIOR)
        match = seniors_table.find_one(d)
        self.assertIsNone(match)
        d["enabled"] = False
        match = seniors_table.find_one(d)
        self.assertIsNotNone(match)

    def test_not_enough_args(self):
        self._test_not_enough_args(valid_body=self.valid_senior)

    def test_no_token(self):
        self._assert_response_code_is_x(data=self.valid_body_deepcopy(), x=401,
                                        client=self.client, path=self.PATH_STORE_SENIOR, r_type='post',
                                        headers=API_KEY_VALUE_PAIR)

    def test_no_apikey(self):
        self._assert_response_code_is_x(data=self.valid_body_deepcopy(), x=401,
                                        client=self.client, path=self.PATH_STORE_SENIOR, r_type='post',
                                        headers=TOKEN_HEADER)


class TestAssignSensorToSenior(TestCaseWithDeletion):
    SENIOR_EXAMPLE = TestStoreSenior.VALID_SENIOR_EXAMPLE
    SENSOR_EXAMPLE = TestStoreSensor.VALID_SENSOR_EXAMPLE
    # It's valid only if the previous entries exist
    VALID_SENSOR_ASSIGNMENT_EXAMPLE = {"seniorId": SENIOR_EXAMPLE["seniorId"],
                                       "sensorId": SENSOR_EXAMPLE["sensorId"]}

    @property
    def collection_name(self):
        return seniors_table

    @property
    def key_with_deletion_marker_value(self):
        return "name"

    def valid_body_deepcopy(self):
        return deepcopy(self.VALID_SENSOR_ASSIGNMENT_EXAMPLE)

    def setUp(self) -> None:
        self.client = TestClient(app)

    def assert_response_code_is_x(self, data, x):
        self._assert_response_code_is_x(data=data, x=x, client=self.client,
                                        path=EndpointPaths.assign_sensor,
                                        r_type='put')

    def test_successful(self):
        post_response(data=self.SENIOR_EXAMPLE, client=self.client, path=EndpointPaths.store_senior)

        post_response(data=self.SENSOR_EXAMPLE, client=self.client, path=EndpointPaths.store_sensor)

        self.assert_response_code_is_x(data=self.VALID_SENSOR_ASSIGNMENT_EXAMPLE, x=200)

    def test_not_enough_args(self):
        self._test_not_enough_args(valid_body=self.VALID_SENSOR_ASSIGNMENT_EXAMPLE)

    def test_no_token(self):
        self._assert_response_code_is_x(data=self.valid_body_deepcopy(), x=401,
                                        client=self.client, path=EndpointPaths.assign_sensor, r_type='post',
                                        headers=API_KEY_VALUE_PAIR)

    def test_no_apikey(self):
        self._assert_response_code_is_x(data=self.valid_body_deepcopy(), x=401,
                                        client=self.client, path=EndpointPaths.assign_sensor, r_type='post',
                                        headers=TOKEN_HEADER)


class TestGetSenior(TestCaseWithDeletion):
    @property
    def collection_name(self):
        return seniors_table

    @property
    def key_with_deletion_marker_value(self):
        return "name"

    def setUp(self) -> None:
        self.PATH_GET_SENIOR = EndpointPaths.get_senior
        self.client = TestClient(app)
        self.valid_senior = TestStoreSenior.VALID_SENIOR_EXAMPLE
        self.valid_senior.update({self.key_with_deletion_marker_value: _DELETION_MARKER_STRING})

    def valid_body_deepcopy(self):
        return deepcopy(self.valid_senior)

    def assert_response_code_is_x(self, data, x):
        return self._assert_response_code_is_x(data, x, client=self.client, path=self.PATH_GET_SENIOR, r_type='get')

    def test_successful(self):
        post_response(data=self.valid_senior, client=self.client, path=EndpointPaths.store_senior)
        r = self.client.get(url=self.PATH_GET_SENIOR,
                            params={"seniorId": self.valid_senior['seniorId']}, headers=final_extra_header)
        self.assertEqual(200, r.status_code)

    def test_non_existent(self):
        r = self.client.get(url=self.PATH_GET_SENIOR, params={"seniorId": 180670668871},
                            headers=final_extra_header)
        self.assertEqual(404, r.status_code)

    def test_no_token(self):
        self._assert_response_code_is_x(data=self.valid_body_deepcopy(), x=401,
                                        client=self.client, path=self.PATH_GET_SENIOR, r_type='post',
                                        headers=API_KEY_VALUE_PAIR)

    def test_no_apikey(self):
        self._assert_response_code_is_x(data=self.valid_body_deepcopy(), x=401,
                                        client=self.client, path=self.PATH_GET_SENIOR, r_type='post',
                                        headers=TOKEN_HEADER)
