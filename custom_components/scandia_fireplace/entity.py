"""Base entity for the Scandia Fireplace integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_info import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MODEL, DOMAIN
from .coordinator import ScandiaCoordinator


class ScandiaEntity(CoordinatorEntity[ScandiaCoordinator]):
    """Common base for all Scandia Fireplace entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ScandiaCoordinator) -> None:
        """Initialise the entity with shared device info."""
        super().__init__(coordinator)
        device = coordinator.device
        model = coordinator.entry.data.get(CONF_MODEL) or (
            device.product_name if device else "Aurora Electric Fire"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)},
            name=coordinator.entry.title,
            manufacturer="Scandia",
            model=model,
        )

    @property
    def available(self) -> bool:
        """Return True when polling works and the device is online."""
        device = self.coordinator.device
        online = device.online if device else False
        return super().available and self.coordinator.data is not None and online

    def _code_value(self, code: str | None) -> Any:
        """Return the current value of a function code, or None if absent."""
        if code is None or self.coordinator.data is None:
            return None
        return self.coordinator.data.get(code)

    def _code_present(self, code: str | None) -> bool:
        """Return True if the device currently reports this function code."""
        return (
            code is not None
            and self.coordinator.data is not None
            and code in self.coordinator.data
        )
