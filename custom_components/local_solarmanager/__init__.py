"""Integration for Local Solar Manager."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import LocalSolarManagerConfigEntry, LocalSolarManagerCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(
    hass: HomeAssistant, entry: LocalSolarManagerConfigEntry
) -> bool:
    """Set up Local Solar Manager from a config entry."""
    coordinator = LocalSolarManagerCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_create_background_task(
        hass,
        coordinator.async_listen_websocket(),
        name="local_solarmanager_websocket",
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: LocalSolarManagerConfigEntry
) -> bool:
    """Unload Local Solar Manager config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
