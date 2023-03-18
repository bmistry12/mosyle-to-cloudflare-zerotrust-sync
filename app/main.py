import logging
from logging.config import fileConfig

import pytoml

from mosyle_client import Mosyle
from cloudflare_client import Cloudflare


log = logging.getLogger(__name__)


def serial_number_sync(self, mac_serials_list_name: str) -> None:
    """Check for discrepancies between serial numbers in Mosyle and CF. Add/remove as necessary."""
    known_serials = self._get_known_serial_numbers(mac_serials_list_name)
    if known_serials == self.mosyle_serial_numbers:
        log.info("Awesome. Mac serial numbers are up to date.")
        return
    to_add = self.mosyle_serial_numbers - known_serials
    log.info("There are %s serial numbers to add...", str(len(to_add)))
    log.info(to_add)
    for add in to_add:
        self._add_serial_number(add)
    known_serials = self._get_known_serial_numbers(mac_serials_list_name)
    # doesn't cater for removing ones that exist after the inital 50
    to_remove = known_serials - self.mosyle_serial_numbers
    log.info("There are %s serial numbers to remove...", str(len(to_remove)))
    log.info(to_remove)
    for remove in to_remove:
        self._remove_serial_number(remove)

if __name__ == "__main__":
    fileConfig("config/logging.config", disable_existing_loggers=False)
    with open("config/configuration.toml", encoding="utf-8") as toml_file:
        config = pytoml.loads(toml_file.read())

    mosyle_client = Mosyle(config["mosyle"])
    mosyle_serial_numbers = mosyle_client.run()
    Cloudflare(
        config["cloudflare"]["api_token"],
        config["cloudflare"]["account_id"],
        mosyle_serial_numbers,
    ).serial_number_sync(config["cloudflare"]["team_list"])

    mosyle_client.get_audit_report(config["s3"]["reports_bucket"])
