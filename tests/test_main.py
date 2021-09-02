from abc import ABC, abstractmethod
from copy import deepcopy
from unittest import TestCase
from fastapi.testclient import TestClient

from app.main import app, homes_table, sensors_table, seniors_table

_DELETION_MARKER_STRING = 'test marker string used for deleting test-entries'


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
    def key_with_deletion_marker(self):
        """
        This key contains the deletion value marker in the database documents.
        On test-class tear-down all entries containing this key-name
        and the deletion-marker as a value, are deleted from the database.

        WARNING: Make sure the selected key is mandatory, otherwise some entries might not be deleted,
        due to how other methods work.
        """
        return ""

    def tearDown(self) -> None:
        self.delete_test_objects_in_db(key=self.key_with_deletion_marker)


class TestCaseWithDeletion(TestEntriesDeletionInDB, TestCase):
    """Implements methods used in most request-tests."""

    def response(self, data, client, path):
        return client.post(path, json=data)

    def _assert_response_code_is_x(self, data, x, client, path):
        response = self.response(data, client, path)
        self.assertEqual(response.status_code, x, msg=str(response.json()))

    @abstractmethod
    def assert_response_code_is_x(self, data, x):
        pass

    # Can't use @abstractmethod test_foo after _test_foo as before
    # because it probably conflicts with how TestCase is implemented (methods starting with "test" are run) and raises:
    # > TypeError: Can't instantiate abstract class TestCaseWithDeletion with abstract methods assert_response_code_is_x
    def _test_not_enough_args(self, valid_body, valid_body_deepcopy_func):
        for key in valid_body.keys():
            d = valid_body_deepcopy_func()
            d.pop(key)
            self.assert_response_code_is_x(data=d, x=422)


class TestStoreHome(TestCaseWithDeletion):
    @property
    def collection_name(self):
        return homes_table

    @property
    def key_with_deletion_marker(self):
        return "name"

    def setUp(self) -> None:
        # (avoiding global import to prevent accidental bugs due to names' similarity)
        from app.main import PATH_STORE_HOME, ALLOWED_HOME_TYPES
        self.PATH_STORE_HOME = PATH_STORE_HOME
        self.ALLOWED_HOME_TYPES = list(ALLOWED_HOME_TYPES)
        self.valid_home = {"homeId": 23897523,
                           self.key_with_deletion_marker: _DELETION_MARKER_STRING,
                           "type": self.ALLOWED_HOME_TYPES[0]}
        self.client = TestClient(app)

    def valid_home_deepcopy(self):
        return deepcopy(self.valid_home)

    def assert_response_code_is_x(self, data, x):
        return self._assert_response_code_is_x(data, x, client=self.client, path=self.PATH_STORE_HOME)

    def test_successful(self):
        d = self.valid_home_deepcopy()
        for home_type in self.ALLOWED_HOME_TYPES:
            d["type"] = home_type
            self.assert_response_code_is_x(data=d, x=201)

    def test_invalid_home_id_0(self):
        d = self.valid_home_deepcopy()
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
        self._test_not_enough_args(valid_body=self.valid_home,
                                   valid_body_deepcopy_func=self.valid_home_deepcopy)


class TestStoreSensor(TestCaseWithDeletion):
    @property
    def collection_name(self):
        return sensors_table

    @property
    def key_with_deletion_marker(self):
        return "hardwareVersion"

    def setUp(self) -> None:
        from app.main import PATH_STORE_SENSOR
        self.PATH_STORE_SENSOR = PATH_STORE_SENSOR
        self.client = TestClient(app)
        self.valid_sensor = {'sensorId': 111,
                             self.key_with_deletion_marker: _DELETION_MARKER_STRING,
                             "softwareVersion": "1.5.15c"}

    def assert_response_code_is_x(self, data, x):
        return self._assert_response_code_is_x(data, x, client=self.client, path=self.PATH_STORE_SENSOR)

    def valid_sensor_deepcopy(self):
        return deepcopy(self.valid_sensor)

    def test_successful(self):
        self.assert_response_code_is_x(data=self.valid_sensor, x=201)

    def test_not_enough_args(self):
        self._test_not_enough_args(valid_body=self.valid_sensor,
                                   valid_body_deepcopy_func=self.valid_sensor_deepcopy)


class TestStoreSenior(TestCaseWithDeletion):
    @property
    def collection_name(self):
        return seniors_table

    @property
    def key_with_deletion_marker(self):
        return "name"

    def setUp(self) -> None:
        from app.main import PATH_STORE_SENIOR
        self.PATH_STORE_SENIOR = PATH_STORE_SENIOR
        self.client = TestClient(app)
        self.valid_senior = {'seniorId': 111,
                             self.key_with_deletion_marker: _DELETION_MARKER_STRING,
                             'homeId': 1,
                             'enabled': False}

    def assert_response_code_is_x(self, data, x):
        return self._assert_response_code_is_x(data, x, client=self.client, path=self.PATH_STORE_SENIOR)

    def valid_senior_deepcopy(self):
        return deepcopy(self.valid_senior)

    def test_successful(self):
        self.assert_response_code_is_x(data=self.valid_senior, x=201)

    def test_store_at_non_existing_home(self):
        d = self.valid_senior_deepcopy()
        # I assume this value will never actually exist in the DB.
        # If it does, this test will falsely fail
        d["homeId"] = 999999999
        self.assert_response_code_is_x(data=d, x=422)

    def test_sensor_id_ignored(self):
        d = self.valid_senior_deepcopy()
        d.update({'sensorId': 5})
        self.assert_response_code_is_x(data=d, x=201)
        d.pop("sensorId")
        match = seniors_table.find_one(d)
        self.assertRaises(KeyError, lambda: match["sensorId"])

    def test_enabled_is_false_by_default(self):
        d = self.valid_senior_deepcopy()
        d["enabled"] = True
        self.response(data=d, client=self.client, path=self.PATH_STORE_SENIOR)
        match = seniors_table.find_one(d)
        self.assertIsNone(match)
        d["enabled"] = False
        match = seniors_table.find_one(d)
        self.assertIsNotNone(match)

    def test_not_enough_args(self):
        self._test_not_enough_args(valid_body=self.valid_senior,
                                   valid_body_deepcopy_func=self.valid_senior_deepcopy)

# TODO test token of Part II (if implemented):
#   response = client.get("/items/foo", headers={"X-Token": "foo"})
#   (tutorial at https://fastapi.tiangolo.com/tutorial/testing/)
