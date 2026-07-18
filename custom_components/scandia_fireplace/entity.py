"""Base entity for the Scandia Fireplace integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_info import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ID, CONF_MODEL, DOMAIN
from .coordinator import ScandiaCoordinator


class ScandiaEntity(CoordinatorEntity[ScandiaCoordinator]):
    """Common base for all Scandia Fireplace entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ScandiaCoordinator) -> None:
        """Initialise the entity with shared device info."""
        super().__init__(coordinator)
        device_id = coordinator.entry.data[CONF_DEVICE_ID]
        model = coordinator.entry.data.get(CONF_MODEL) or "Aurora Electric Fire"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=coordinator.entry.title,
            manufacturer="Scandia",
            model=model,
        )

    @property
    def available(self) -> bool:
        """Return True when the last poll succeeded."""
        return super().available and self.coordinator.data is not None

    def _dp_value(self, dp: str | None) -> Any:
        """Return the current value of a data point, or None if absent."""
        if dp is None or self.coordinator.data is None:
            return None
        return self.coordinator.data.get(dp)

    def _dp_present(self, dp: str | None) -> bool:
        """Return True if the device currently reports this data point."""
        return dp is not None and self.coordinator.data is not None and dp in self.coordinator.data
