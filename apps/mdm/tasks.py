import json
import os
import structlog

from django.db.models import Q

from requests_ratelimiter import LimiterSession
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from apps.odk_publish.models import AppUser
from apps.mdm.models import Policy, Device


logger = structlog.getLogger(__name__)


def get_tinymdm_session():
    """
    Creates a requests session suitable for use with the TinyMDM API. Should be
    shared across all requests during a to avoid hitting the rate limit.
    """
    session = LimiterSession(per_second=5)

    headers = {
        # TODO: Move these to secure credential store
        "X-Tinymdm-Manager-Apikey-Public": os.getenv("TINYMDM_APIKEY_PUBLIC"),
        "X-Tinymdm-Manager-Apikey-Secret": os.getenv("TINYMDM_APIKEY_SECRET"),
        "X-Account-Id": os.getenv("TINYMDM_ACCOUNT_ID"),
    }
    if not all(headers.values()):
        logger.warning("TinyMDM API credentials not configured.")
        return None
    session.headers.update(headers)

    retries = Retry(
        total=5,
        backoff_factor=0.1,
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))

    return session


def update_existing_devices(policy, mdm_devices):
    """
    Updates existing devices in our datatabase based on the full list
    of mdm_devices returned form the TinyMDM API.
    """
    devices_by_id = {device["id"]: device for device in mdm_devices}
    devices_by_serial = {device["serial_number"]: device for device in mdm_devices}

    our_devices = Device.objects.filter(
        Q(policy=policy)
        & (Q(device_id__in=devices_by_id.keys()) | Q(serial_number__in=devices_by_serial.keys()))
    )

    for our_device in our_devices:
        if our_device.device_id:
            mdm_device = devices_by_id.get(our_device.device_id)
        else:
            mdm_device = devices_by_serial.get(our_device.serial_number)
        if not mdm_device:
            # TODO: Remove the device from our database?
            continue
        our_device.serial_number = mdm_device["serial_number"] or ""
        our_device.device_id = mdm_device["id"]
        our_device.name = mdm_device["nickname"] or mdm_device["name"]
        our_device.raw_mdm_device = mdm_device

    logger.debug("Updating existing devices", our_devices=our_devices)
    Device.objects.bulk_update(
        our_devices, fields=["serial_number", "device_id", "raw_mdm_device", "name"]
    )
    return our_devices


def create_new_devices(policy, mdm_devices):
    """
    Creates new devices in our database based on the mdm_devices
    received from the API. This list must not contain devices that
    already exist in our database.
    """
    mdm_devices_to_create = [
        Device(
            policy=policy,
            serial_number=mdm_device["serial_number"] or "",
            device_id=mdm_device["id"],
            name=mdm_device["nickname"] or mdm_device["name"],
            raw_mdm_device=mdm_device,
        )
        for mdm_device in mdm_devices
    ]
    logger.debug("Creating new devices", mdm_devices_to_create=mdm_devices_to_create)
    Device.objects.bulk_create(mdm_devices_to_create)
    return mdm_devices_to_create


def pull_devices(session, policy):
    """
    Retrieves devices from TinyMDM and updates or creates the records in our
    database for those devices.
    """
    url = "https://www.tinymdm.net/api/v1/devices"
    querystring = {"policy_id": policy.policy_id, "per_page": 1000}
    logger.info("Pulling devices from TinyMDM", url=url, querystring=querystring)
    response = session.request("GET", url, params=querystring)
    response.raise_for_status()
    mdm_devices = response.json()["results"]
    our_devices = update_existing_devices(policy, mdm_devices)
    our_device_ids = {device.device_id for device in our_devices}
    mdm_devices_to_create = [
        mdm_device for mdm_device in mdm_devices if mdm_device["id"] not in our_device_ids
    ]
    create_new_devices(policy, mdm_devices_to_create)


def push_device_config(session, device: Device):
    """
    Updates "custom_field_1" on the device's user record in TinyMDM
    with the ODK Collect configuration necessary to attach to the devices project.

    https://www.tinymdm.net/mobile-device-management/api/#put-/users/-id-
    """
    logger.debug("Syncing device", device=device)
    if (device.app_user_name) and (
        app_user := AppUser.objects.filter(
            name=device.app_user_name, project=device.policy.project
        ).first()
    ):
        qr_code_data = json.dumps(app_user.qr_code_data, separators=(",", ":"))
    else:
        qr_code_data = ""
    user_id = device.raw_mdm_device["user_id"]
    url = f"https://www.tinymdm.net/api/v1/users/{user_id}"
    device_name = device.raw_mdm_device["nickname"] or device.raw_mdm_device["name"]
    data = {
        "name": f"{device.app_user_name}-{device_name}",
        "custom_field_1": qr_code_data,
    }
    logger.debug("Updating user", url=url, user_id=user_id, data=data)
    response = session.request("PUT", url, json=data)
    response.raise_for_status()
    # Send a message to the user to inform them of the update and trigger a policy reload
    url = "https://www.tinymdm.net/api/v1/actions/message"
    logger.debug("Sending message to device", url=url, user_id=user_id)
    data = {
        "message": (
            f"This device has been configured for Center Number {device.app_user_name}.\n\n"
            "Please close and re-open the HNEC Collect app to see the new project.\n\n"
            "In case of any issues, please open the TinyMDM app and reload the policy "
            "or restart the device."
        ),
        "title": "HNEC Collect Project Update",
        "devices": [device.device_id],
    }
    response = session.request("POST", url, json=data)
    response.raise_for_status()


def sync_policy(session, policy):
    """
    Synchronizes the remote TinyMDM device list with our database,
    and updates the device (user) configuration in TinyMDM based on the
    configured ODK Central app users.
    """
    logger.info("Syncing policy to TinyMDM devices", policy=policy)
    pull_devices(session, policy)
    for device in policy.devices.exclude(app_user_name="").select_related("policy").all():
        push_device_config(session, device)


def sync_policies():
    """
    Synchronizes all configured policies with TinyMDM and updates the applicable
    device configurations.
    """
    logger.info("Syncing policies with TinyMDM")
    session = get_tinymdm_session()
    for policy in Policy.objects.all():
        sync_policy(session, policy)
