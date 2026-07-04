"""Constants for the Flowwave integration."""

DOMAIN = "flowwave"
INGEST_URL = "https://flowwave.nl/api/ingest"

CONF_TOKEN = "token"
CONF_CONSUMPTION = "consumption"
CONF_PRODUCTION = "production"
CONF_SOLAR = "solar"
CONF_GAS = "gas"
CONF_VOLTAGE = "voltage"
CONF_SCAN_INTERVAL = "scan_interval"

# every 10 s matches the pace of a P1 meter; the server accepts ~6/min per device
DEFAULT_SCAN_INTERVAL = 10
