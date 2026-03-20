"""Support for Local Solar Manager sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import (
    LocalSolarManagerConfigEntry,
    LocalSolarManagerData,
    LocalSolarManagerDeviceData,
)
from .entity import LocalSolarManagerDeviceEntity, LocalSolarManagerEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class LocalSolarManagerSensorDescription(SensorEntityDescription):
    """Describe a Local Solar Manager sensor."""

    value_fn: Callable[[LocalSolarManagerData], float]


@dataclass(frozen=True, kw_only=True)
class LocalSolarManagerDeviceSensorDescription(SensorEntityDescription):
    """Describe a Local Solar Manager device sensor."""

    value_fn: Callable[[LocalSolarManagerDeviceData], float | None]
    device_types: frozenset[str] | None = None  # None = all device types


SENSOR_DESCRIPTIONS: tuple[LocalSolarManagerSensorDescription, ...] = (
    LocalSolarManagerSensorDescription(
        key="consumption_power",
        translation_key="consumption_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.consumption_power,
    ),
    LocalSolarManagerSensorDescription(
        key="production_power",
        translation_key="production_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.production_power,
    ),
    LocalSolarManagerSensorDescription(
        key="battery_charging_power",
        translation_key="battery_charging_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.battery_charging_power,
    ),
    LocalSolarManagerSensorDescription(
        key="battery_discharging_power",
        translation_key="battery_discharging_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.battery_discharging_power,
    ),
    LocalSolarManagerSensorDescription(
        key="consumption_energy",
        translation_key="consumption_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.consumption_energy,
    ),
    LocalSolarManagerSensorDescription(
        key="production_energy",
        translation_key="production_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.production_energy,
    ),
    LocalSolarManagerSensorDescription(
        key="battery_charging_energy",
        translation_key="battery_charging_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.battery_charging_energy,
    ),
    LocalSolarManagerSensorDescription(
        key="battery_discharging_energy",
        translation_key="battery_discharging_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.battery_discharging_energy,
    ),
    LocalSolarManagerSensorDescription(
        key="self_consumption_energy",
        translation_key="self_consumption_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.self_consumption_energy,
    ),
    LocalSolarManagerSensorDescription(
        key="direct_pv_consumption_energy",
        translation_key="direct_pv_consumption_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.direct_pv_consumption_energy,
    ),
    LocalSolarManagerSensorDescription(
        key="grid_import_energy",
        translation_key="grid_import_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.grid_import_energy,
    ),
    LocalSolarManagerSensorDescription(
        key="grid_export_energy",
        translation_key="grid_export_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.grid_export_energy,
    ),
)

DEVICE_SENSOR_DESCRIPTIONS: tuple[LocalSolarManagerDeviceSensorDescription, ...] = (
    LocalSolarManagerDeviceSensorDescription(
        key="power",
        translation_key="device_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.power,
    ),
    LocalSolarManagerDeviceSensorDescription(
        key="soc",
        translation_key="device_soc",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.soc,
    ),
    # Heat pump + water heater
    LocalSolarManagerDeviceSensorDescription(
        key="temperature",
        translation_key="device_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.temperature,
        device_types=frozenset({"heatpump", "waterheater"}),
    ),
    LocalSolarManagerDeviceSensorDescription(
        key="active_device",
        translation_key="device_active",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.active_device,
        device_types=frozenset({"heatpump", "waterheater"}),
    ),
    # Heat pump only
    LocalSolarManagerDeviceSensorDescription(
        key="operation_state",
        translation_key="device_operation_state",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.operation_state,
        device_types=frozenset({"heatpump"}),
    ),
    LocalSolarManagerDeviceSensorDescription(
        key="heating_adjustment",
        translation_key="device_heating_adjustment",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.heating_adjustment,
        device_types=frozenset({"heatpump"}),
    ),
    # Water heater only
    LocalSolarManagerDeviceSensorDescription(
        key="imported_energy",
        translation_key="device_imported_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda device: device.imported_energy,
        device_types=frozenset({"waterheater"}),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LocalSolarManagerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Local Solar Manager sensors based on a config entry."""
    coordinator = entry.runtime_data

    entities: list[SensorEntity] = [
        LocalSolarManagerSensorEntity(
            entry=entry,
            coordinator=coordinator,
            description=description,
        )
        for description in SENSOR_DESCRIPTIONS
    ]

    for device in coordinator.data.devices:
        for description in DEVICE_SENSOR_DESCRIPTIONS:
            # Only create the SoC sensor for devices that report it
            if description.key == "soc" and device.soc is None:
                continue
            # Skip device-type-specific sensors for non-matching device types
            if (
                description.device_types is not None
                and device.device_type not in description.device_types
            ):
                continue
            entities.append(
                LocalSolarManagerDeviceSensorEntity(
                    entry=entry,
                    coordinator=coordinator,
                    description=description,
                    device=device,
                )
            )

    async_add_entities(entities)


class LocalSolarManagerSensorEntity(LocalSolarManagerEntity, SensorEntity):
    """Define a Local Solar Manager sensor."""

    entity_description: LocalSolarManagerSensorDescription

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)


class LocalSolarManagerDeviceSensorEntity(LocalSolarManagerDeviceEntity, SensorEntity):
    """Define a Local Solar Manager device sensor."""

    entity_description: LocalSolarManagerDeviceSensorDescription

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        for device in self.coordinator.data.devices:
            if device.device_id == self._device_id:
                return self.entity_description.value_fn(device)
        return None
