"""Base entity for the Scandia Fireplace integration."""

from __future__ import annotations

from homeassistant.helpers.device_info import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ScandiaBaseCoordinator


class ScandiaEntity(CoordinatorEntity[ScandiaBaseCoordinator]):
    """Common base for all Scandia Fireplace entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ScandiaBaseCoordinator) -> None:
        """Initialise the entity with shared device info."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)},
            name=coordinator.entry.title,
            manufacturer="Scandia",
            model=coordinator.device_model or "Aurora Electric Fire",
        )

    @property
    def available(self) -> bool:
        """Return True when polling works and the device is online."""
        return (
            super().available
            and self.coordinator.data is not None
            and self.coordinator.device_online
        )
