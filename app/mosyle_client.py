import requests

from base64 import b64encode
from datetime import date, datetime
from json import dumps
from typing import Dict, List

import boto3

from botocore.exceptions import ClientError


class MosyleError(Exception):
    pass


class Mosyle:
    def __init__(self, mosyle_config: Dict) -> None:
        self.mosyle_api_token: str = mosyle_config["api_token"]
        self.mosyle_email: str = mosyle_config["email"]
        self.mosyle_pwd: str = mosyle_config["password"]
        self.base_url = "https://businessapi.mosyle.com/v1"
        self.mac_devices: list = []

    @staticmethod
    def _get_data_for_query(page_number: int) -> dict:
        data = {
            "operation": "list",
            "options": {
                "os": "mac",
                "page": page_number,
            },
        }
        return data

    def _request(self, path: str, data: str) -> List[dict]:
        """Put request."""
        auth = b64encode((self.mosyle_email + ":" + self.mosyle_pwd).encode()).decode("ascii")
        response = requests.post(
            self.base_url + path,
            headers={
                "accesstoken": self.mosyle_api_token,
                "Content-Type": "application/json",
                "Authorization": "Basic " + auth,
            },
            data=data,
            timeout=60,
        )
        response.raise_for_status()
        response_json = response.json()
        if "status" in response_json and response_json["status"] == "OK":
            return response_json["response"]
        raise MosyleError("The only request methods currently supported are: POST")  # noqa: TC003

    def _get_mac_devices(self) -> None:
        """Get mac devices and add to self.mac_devices."""
        page_number: int = 1
        mac_response = self._request("/devices", dumps(self._get_data_for_query(page_number)))[0]
        self.mac_devices = list(mac_response.get("devices", []))
        rows = mac_response.get("rows", 0)
        while len(self.mac_devices) < rows:
            # more devices than on the page (max 50 per page)...get from the next
            page_number = page_number + 1
            next_response = self._request("/devices", dumps(self._get_data_for_query(page_number)))[0]
            self.mac_devices += list(next_response.get("devices", []))

    @staticmethod
    def _upload_to_s3(bucket: str, file_name: str) -> None:
        """Upload report to S3."""
        try:
            s3_client = boto3.client("s3")
            object_name = "mosyle-device-reports/" + file_name
            _ = s3_client.upload_file(file_name, bucket, object_name)
        except ClientError as error:
            raise ClientError("Failed to upload file to S3: ", error) from error  # noqa: TC003

    def get_audit_report(self, bucket: str) -> None:
        """Get a report of devices registered and user/os details."""
        report_info: list = []
        for device in self.mac_devices:
            report_info.append(
                {
                    "serialNumber": device["serial_number"],
                    "deviceName": device["device_name"],
                    "deviceModel": device["device_model_name"],
                    "osVersion": device["osversion"],
                    "userID": device["userid"] if "userid" in device else "",
                    "username": device["username"] if "username" in device else "",
                    "userType": device["usertype"] if "usertype" in device else "",
                }
            )
        file_name = f"mosyle-device-report-{date.today().strftime('%d-%m-%Y')}-h{datetime.now().hour}-m{datetime.now().minute}"  # noqa: E501 pylint: disable=line-too-long
        try:
            with open(file_name, "w", encoding="utf-8") as json_file:
                json_file.write(dumps(report_info, indent=4))
        except IOError as error:
            raise MosyleError(str(error)) from error  # noqa: TC003
        self._upload_to_s3(bucket, file_name)

    def run(self) -> set:
        """Get all managed mac serial numbers."""
        self._get_mac_devices()
        serial_numbers = {device["serial_number"] for device in self.mac_devices if "serial_number" in device}
        return serial_numbers

