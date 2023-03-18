import enum
import requests

from logging import getLogger
from retry import retry
from typing import Optional


log = getLogger(__name__)


class Request(enum.Enum):
    GET = "GET"
    PATCH = "PATCH"


class CloudflareError(Exception):
    pass


class Cloudflare:
    def __init__(self, cf_api_token: str, account_id: str, serial_numbers: set) -> None:
        self.cf_api_token: str = cf_api_token
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}"
        self.mosyle_serial_numbers = serial_numbers
        self.uuid = ""

    @retry(CloudflareError, tries=5, delay=1, logger=log)
    def _request(self, path: str, method: Request, data: Optional[str] = None) -> dict:
        """Get or Patch request."""
        token = f"Bearer {self.cf_api_token}"
        try:
            response = requests.request(
                method=method.value,
                url=self.base_url + path,
                headers={
                    "Authorization": token,
                    "Content-Type": "application/json",
                },
                data=data,
                timeout=60,
            )
            response.raise_for_status()
            response_json = response.json()
        except requests.exceptions.HTTPError as err:
            if response.status_code == 409:
                # 409 Client Error: Conflict for url
                return {"skip": True}
            else:
                raise CloudflareError(err) from err
        return response_json

    def _get_known_serial_numbers(self, mac_serials_list_name: str) -> set:
        """
        Get serial numbers in Cloudflare teams gateway list.

        Note: this only gets the first 50. Pagination doesn't seem to work.
        """
        known_serials: set = set()
        lists = self._request("/gateway/lists", Request.GET).get("result", [])
        for item in lists:
            if item["name"] == mac_serials_list_name:
                self.uuid = item["id"]
                log.info("There are currently %s serial numbers", item["count"])
        if self.uuid:
            response = self._request(f"/gateway/lists/{self.uuid}/items", Request.GET).get("result", [])
            known_serials = {item["value"] for item in response}
        return known_serials

    def _add_serial_number(self, serial_number: str) -> None:
        """Add serial number to CF list."""
        params = '{"append":[{"value": "%s"}]}' % serial_number  # pylint: disable=consider-using-f-string
        update = self._request(f"/gateway/lists/{self.uuid}", Request.PATCH, f"{params}")
        if update.get("success", False):
            log.info("Added serial number: %s", serial_number)
        elif update.get("skip", False):
            log.info("Serial number %s already exists...skipping", serial_number)
        else:
            raise CloudflareError(f"Unable to add serial number: {serial_number}")

    def _remove_serial_number(self, serial_number: str) -> None:
        """Remove serial number from CF list."""
        params = '{"remove":["%s"]}' % serial_number  # pylint: disable=consider-using-f-string
        update = self._request(f"/gateway/lists/{self.uuid}", Request.PATCH, f"{params}")
        if update.get("success", False):
            log.info("Removed serial number: %s", serial_number)
        else:
            raise CloudflareError(f"Unable to remove serial number: {serial_number}")

