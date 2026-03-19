"""Base entity for the Local Solar Manager integration."""

from __future__ import annotations

from homeassistant.const import CONF_HOST
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import (
    LocalSolarManagerConfigEntry,
    LocalSolarManagerCoordinator,
    LocalSolarManagerDeviceData,
)


class LocalSolarManagerEntity(CoordinatorEntity[LocalSolarManagerCoordinator]):
    """Define a Local Solar Manager entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: LocalSolarManagerConfigEntry,
        coordinator: LocalSolarManagerCoordinator,
        description: EntityDescription,
    ) -> None:
        """Initialize the Local Solar Manager entity."""
        super().__init__(coordinator=coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            configuration_url=f"http://{entry.data[CONF_HOST]}",
            manufacturer="Solar Manager AG",
            name="Solar Manager",
        )


class LocalSolarManagerDeviceEntity(CoordinatorEntity[LocalSolarManagerCoordinator]):
    """Define a Local Solar Manager per-device entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: LocalSolarManagerConfigEntry,
        coordinator: LocalSolarManagerCoordinator,
        description: EntityDescription,
        device: LocalSolarManagerDeviceData,
    ) -> None:
        """Initialize the Local Solar Manager device entity."""
        super().__init__(coordinator=coordinator)
        self.entity_description = description
        self._device_id = device.device_id
        self._attr_unique_id = f"{entry.entry_id}_{device.device_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_{device.device_id}")},
            name=device.name or device.device_id,
            model=device.description,
            model_id=device.device_type,
            via_device=(DOMAIN, entry.entry_id),
        )
