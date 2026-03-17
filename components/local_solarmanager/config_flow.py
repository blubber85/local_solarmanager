"""Config flow to configure the Local Solar Manager integration."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import CONF_API_KEY, DOMAIN, LOGGER


class LocalSolarManagerFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a Local Solar Manager config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            api_key = user_input.get(CONF_API_KEY)

            try:
                await self._test_connection(host, api_key)
            except TimeoutError:
                errors[CONF_HOST] = "cannot_connect"
            except aiohttp.ClientError:
                errors[CONF_HOST] = "cannot_connect"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                self._async_abort_entries_match({CONF_HOST: host})
                return self.async_create_entry(
                    title=host,
                    data=user_input,
                )
        else:
            user_input = {}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST, default=user_input.get(CONF_HOST)
                    ): TextSelector(TextSelectorConfig(autocomplete="off")),
                    vol.Optional(
                        CONF_API_KEY, default=user_input.get(CONF_API_KEY, "")
                    ): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
                }
            ),
            errors=errors,
        )

    async def _test_connection(self, host: str, api_key: str | None) -> None:
        """Test if we can connect to the Solar Manager local API."""
        session = async_get_clientsession(self.hass, verify_ssl=False)
        headers: dict[str, str] = {}
        if api_key:
            headers["X-API-Key"] = api_key

        url = f"http://{host}/v2/point"
        async with asyncio.timeout(10):
            response = await session.get(url, headers=headers)
            response.raise_for_status()
