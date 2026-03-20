"""Data update coordinator for Local Solar Manager."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_API_KEY, DOMAIN, LOGGER

_WS_RECONNECT_DELAY_INITIAL = 5
_WS_RECONNECT_DELAY_MAX = 60


@dataclass(kw_only=True)
class LocalSolarManagerDeviceData:
    """Combined runtime and metadata for a single connected device.

    Runtime data (power, soc, signal) comes from the devices list in /v2/point.
    Metadata (name, device_type, description) comes from /v2/devices, matched on device_id.
    """

    device_id: str
    name: str | None
    device_type: str | None
    description: str | None
    signal: str
    power: float
    soc: float | None
    # Heat pump specific (device_type == "heatpump")
    temperature: float | None
    active_device: int | None
    heating_adjustment: float | None
    operation_state: int | None
    # Water heater specific (device_type == "waterheater")
    imported_energy: float | None


@dataclass(kw_only=True)
class LocalSolarManagerData:
    """Class to hold data from the Local Solar Manager API."""

    timestamp: str
    version: int
    consumption_power: float
    production_power: float
    battery_charging_power: float
    battery_discharging_power: float
    consumption_energy: float
    production_energy: float
    battery_charging_energy: float
    battery_discharging_energy: float
    self_consumption_energy: float
    direct_pv_consumption_energy: float
    grid_import_energy: float
    grid_export_energy: float
    devices: list[LocalSolarManagerDeviceData]


type LocalSolarManagerConfigEntry = ConfigEntry[LocalSolarManagerCoordinator]


class LocalSolarManagerCoordinator(DataUpdateCoordinator[LocalSolarManagerData]):
    """Coordinator to manage Local Solar Manager data via WebSocket push."""

    config_entry: LocalSolarManagerConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: LocalSolarManagerConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
        )
        self._host = entry.data[CONF_HOST]
        self._api_key: str | None = entry.data.get(CONF_API_KEY) or None
        self._session = async_get_clientsession(hass, verify_ssl=False)
        self._devices_metadata: dict[str, dict] = {}

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP/WS headers including optional API key."""
        headers: dict[str, str] = {}
        if self._api_key:
            headers["X-API-Key"] = self._api_key
        return headers

    async def _async_update_data(self) -> LocalSolarManagerData:
        """Fetch initial data from HTTP endpoints.

        Called once during setup via async_config_entry_first_refresh.
        Subsequent updates arrive via the WebSocket listener.
        """
        headers = self._build_headers()
        url_point = f"http://{self._host}/v2/point"
        url_devices = f"http://{self._host}/v2/devices"

        try:
            async with asyncio.timeout(10):
                point_response, devices_response = await asyncio.gather(
                    self._session.get(url_point, headers=headers),
                    self._session.get(url_devices, headers=headers),
                )
                point_response.raise_for_status()
                devices_response.raise_for_status()
                point_data, devices_data = await asyncio.gather(
                    point_response.json(),
                    devices_response.json(),
                )
        except TimeoutError as err:
            raise UpdateFailed(f"Timeout connecting to {self._host}") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with {self._host}: {err}") from err

        self._devices_metadata = {
            d["deviceId"]: d for d in devices_data if "deviceId" in d
        }
        return self._parse_point_data(point_data)

    def _parse_point_data(self, point_data: dict) -> LocalSolarManagerData:
        """Parse a /v2/point-style payload and merge with cached device metadata."""
        devices = [
            LocalSolarManagerDeviceData(
                device_id=d["_id"],
                name=self._devices_metadata.get(d["_id"], {}).get("name"),
                device_type=self._devices_metadata.get(d["_id"], {}).get("type"),
                description=self._devices_metadata.get(d["_id"], {}).get("description"),
                signal=d.get("signal", ""),
                power=d.get("power", 0.0),
                soc=d.get("soc"),
                temperature=d.get("temperature"),
                active_device=d.get("activeDevice"),
                heating_adjustment=d.get("heatingAdjustment"),
                operation_state=d.get("operationState"),
                imported_energy=d.get("iWh"),
            )
            for d in point_data.get("devices", [])
            if "_id" in d
        ]

        return LocalSolarManagerData(
            timestamp=point_data.get("t", ""),
            version=point_data.get("v", 0),
            consumption_power=point_data.get("cW", 0),
            production_power=point_data.get("pW", 0),
            battery_charging_power=point_data.get("bcW", 0),
            battery_discharging_power=point_data.get("bdW", 0),
            consumption_energy=point_data.get("cWh", 0),
            production_energy=point_data.get("pWh", 0),
            battery_charging_energy=point_data.get("bcWh", 0),
            battery_discharging_energy=point_data.get("bdWh", 0),
            self_consumption_energy=point_data.get("scWh", 0),
            direct_pv_consumption_energy=point_data.get("cPvWh", 0),
            grid_import_energy=point_data.get("iWh", 0),
            grid_export_energy=point_data.get("eWh", 0),
            devices=devices,
        )

    async def async_listen_websocket(self) -> None:
        """Connect to /v2/stream and push updates; reconnect on failure.

        Intended to be run as a background task via
        entry.async_create_background_task so it is automatically cancelled
        when the config entry is unloaded.
        """
        url = f"ws://{self._host}/v2/stream"
        headers = self._build_headers()
        retry_delay = _WS_RECONNECT_DELAY_INITIAL

        while True:
            try:
                async with self._session.ws_connect(
                    url, headers=headers, ssl=False
                ) as ws:
                    LOGGER.debug("WebSocket connected to %s", self._host)
                    retry_delay = _WS_RECONNECT_DELAY_INITIAL
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                point_data = json.loads(msg.data)
                            except json.JSONDecodeError as err:
                                LOGGER.warning(
                                    "Ignoring malformed WebSocket message: %s", err
                                )
                                continue
                            LOGGER.info(f"data: {point_data}")
                            self.async_set_updated_data(
                                self._parse_point_data(point_data)
                            )
                        elif msg.type in (
                            aiohttp.WSMsgType.CLOSED,
                            aiohttp.WSMsgType.ERROR,
                        ):
                            LOGGER.debug(
                                "WebSocket closed/error from %s, reconnecting",
                                self._host,
                            )
                            break
            except aiohttp.ClientError as err:
                LOGGER.warning(
                    "WebSocket error for %s: %s. Retrying in %d s.",
                    self._host,
                    err,
                    retry_delay,
                )
            except asyncio.CancelledError:
                LOGGER.debug("WebSocket listener for %s cancelled", self._host)
                raise

            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, _WS_RECONNECT_DELAY_MAX)
