import json
import pytest
from requests.sessions import Session

from apps.mdm import tasks
from apps.odk_publish.etl.odk.constants import DEFAULT_COLLECT_SETTINGS
from tests.odk_publish.factories import AppUserFactory

from .factories import DeviceFactory, PolicyFactory


@pytest.mark.django_db
class TestTasks:
    TINYMDM_ENV_VARS = ("TINYMDM_APIKEY_PUBLIC", "TINYMDM_APIKEY_SECRET", "TINYMDM_ACCOUNT_ID")

    @pytest.fixture
    def policy(self):
        return PolicyFactory()

    @pytest.fixture
    def devices(self, policy):
        """Create 6 Devices, one with a blank device_id."""
        return DeviceFactory.create_batch(5, policy=policy) + [
            DeviceFactory(policy=policy, device_id="")
        ]

    @pytest.fixture
    def del_tinymdm_env_vars(self, monkeypatch):
        """Delete environment variables for TinyMDM API credentials, if they exist."""
        for var in self.TINYMDM_ENV_VARS:
            monkeypatch.delenv(var, raising=False)

    @pytest.fixture
    def set_tinymdm_env_vars(self, monkeypatch):
        """Set environment variables for TinyMDM API credentials to fake values."""
        for var in self.TINYMDM_ENV_VARS:
            monkeypatch.setenv(var, "test")

    def get_raw_mdm_device(self, device):
        """Create data for the Device.raw_mdm_device field based on other fields' values."""
        return {
            "id": device.device_id,
            "serial_number": device.serial_number,
            "name": device.name,
            "nickname": device.name,
            "user_id": f"user{device.device_id}",
        }

    @pytest.fixture
    def devices_response(self, devices):
        """Mock response for a TinyMDM device listing API request."""
        return {
            "results": [
                # Existing devices, which should be updated in the DB
                {
                    "id": device.device_id,
                    "serial_number": (
                        f"updated-{device.serial_number}"
                        if device.device_id
                        else device.serial_number
                    ),
                    "name": f"updated-name-{device.name}",
                    "nickname": f"updated-nickname-{device.name}",
                    "user_id": f"user{device.device_id}",
                }
                for device in devices
            ]
            + [
                # New devices, which should be created in the DB
                self.get_raw_mdm_device(device)
                for device in DeviceFactory.build_batch(4)
            ]
        }

    @pytest.fixture
    def device(self, request, policy):
        """Create one Device. If request.param is True, create an AppUser with
        the name in the device's app_user_name field and with qr_code_data set.
        """
        device = DeviceFactory.build(policy=policy)
        device.raw_mdm_device = self.get_raw_mdm_device(device)
        if request.param:
            AppUserFactory(
                name=device.app_user_name,
                project=policy.project,
                qr_code_data=DEFAULT_COLLECT_SETTINGS,
            )
        else:
            device.app_user_name = ""
        device.save()
        return device

    @pytest.fixture
    def policies(self, policy):
        return PolicyFactory.create_batch(2) + [policy]

    def test_get_tinymdm_session_without_env_variables(self, del_tinymdm_env_vars):
        """Ensure get_tinymdm_session() returns None if the environment variables
        for TinyMDM API credentials are not set.
        """
        assert tasks.get_tinymdm_session() is None

    def test_get_tinymdm_session_with_env_variables(self, set_tinymdm_env_vars):
        """Ensure get_tinymdm_session() returns a requests Session object if the
        environment variables for TinyMDM API credentials are set.
        """
        assert isinstance(tasks.get_tinymdm_session(), Session)

    def test_pull_devices(self, policy, requests_mock, devices_response, set_tinymdm_env_vars):
        """Ensures calling pull_devices() updates and creates Devices as expected."""
        requests_mock.get("https://www.tinymdm.net/api/v1/devices", json=devices_response)
        session = tasks.get_tinymdm_session()
        tasks.pull_devices(session, policy)

        # There should be 10 devices now in the DB. 4 are new
        assert policy.devices.count() == 10
        # Ensure the devices have the expected data from the API response
        db_devices = policy.devices.in_bulk(field_name="device_id")
        for device in devices_response["results"]:
            db_device = db_devices[device["id"]]
            assert db_device.serial_number == device["serial_number"]
            assert db_device.name == device["nickname"] or device["name"]
            assert db_device.raw_mdm_device == device

    @pytest.mark.parametrize("device", [False, True], indirect=True)
    def test_push_device_config(self, device, requests_mock, set_tinymdm_env_vars):
        """Ensures push_device_config() makes the expected API requests."""
        user_update_request = requests_mock.put(
            f"https://www.tinymdm.net/api/v1/users/{device.raw_mdm_device['user_id']}"
        )
        message_request = requests_mock.post("https://www.tinymdm.net/api/v1/actions/message")
        session = tasks.get_tinymdm_session()
        tasks.push_device_config(session, device)

        if device.app_user_name:
            # Get QR code data from the AppUser
            app_user = device.policy.project.app_users.get(name=device.app_user_name)
            qr_code_data = json.dumps(app_user.qr_code_data, separators=(",", ":"))
        else:
            qr_code_data = ""

        device_name = device.raw_mdm_device["nickname"] or device.raw_mdm_device["name"]

        assert user_update_request.called_once
        assert user_update_request.last_request.json() == {
            "name": f"{device.app_user_name}-{device_name}",
            "custom_field_1": qr_code_data,
        }
        assert message_request.called_once
        assert message_request.last_request.json() == {
            "message": (
                f"This device has been configured for Center Number {device.app_user_name}.\n\n"
                "Please close and re-open the HNEC Collect app to see the new project.\n\n"
                "In case of any issues, please open the TinyMDM app and reload the policy "
                "or restart the device."
            ),
            "title": "HNEC Collect Project Update",
            "devices": [device.device_id],
        }

    def test_sync_policy(self, policy, devices, mocker, set_tinymdm_env_vars):
        """Ensure calling sync_policy() calls pull_devices() for the specified policy
        and push_device_config() for the policy's devices whose app_user_name field is set.
        """
        # Make app_user_name blank for some devices
        policy.devices.filter(id__in=[d.id for d in devices][:3]).update(app_user_name="")
        devices_to_push = policy.devices.exclude(app_user_name="")

        mock_pull_devices = mocker.patch("apps.mdm.tasks.pull_devices")
        mock_push_device_config = mocker.patch("apps.mdm.tasks.push_device_config")
        session = tasks.get_tinymdm_session()
        tasks.sync_policy(session, policy)

        mock_pull_devices.assert_called_once()
        # push_device_config should be called only for the devices where
        # app_user_name is set
        mock_push_device_config.assert_has_calls(
            [mocker.call(session, device) for device in devices_to_push], any_order=True
        )
        assert mock_push_device_config.call_count == len(devices_to_push)

    def test_sync_policies(self, policies, mocker, set_tinymdm_env_vars):
        """Ensure calling sync_policies() calls sync_policy() for all policies."""
        mock_sync_policy = mocker.patch("apps.mdm.tasks.sync_policy")
        tasks.sync_policies()

        assert mock_sync_policy.call_count == len(policies)
        for call in mock_sync_policy.call_list_args:
            assert isinstance(call.args[0], Session)
            assert call.args[1] in policies
