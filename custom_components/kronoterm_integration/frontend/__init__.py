"""Javascript module registration for kronoterm_integration."""

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace import LovelaceData
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later

from ..const import JSMODULES, URL_BASE

_LOGGER = logging.getLogger(__name__)


class JSModuleRegistration:
    """Register frontend JavaScript modules."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.lovelace: LovelaceData = self.hass.data.get("lovelace")

    async def async_register(self):
        await self._async_register_static_path()

        if self.lovelace.mode == "storage":
            await self._async_wait_for_lovelace_resources()

    async def _async_register_static_path(self):
        try:
            await self.hass.http.async_register_static_paths(
                [StaticPathConfig(URL_BASE, Path(__file__).parent, cache_headers=False)]
            )
            _LOGGER.debug("Registered static path %s", URL_BASE)
        except RuntimeError:
            _LOGGER.debug("Static path %s already registered", URL_BASE)

    async def _async_wait_for_lovelace_resources(self):
        async def _check_resources(now):
            if self.lovelace.resources.loaded:
                await self._async_register_modules()
            else:
                _LOGGER.debug("Lovelace resources not loaded yet, retrying in 5s...")
                async_call_later(self.hass, 5, _check_resources)

        await _check_resources(0)

    async def _async_register_modules(self):
        _LOGGER.info("Registering frontend modules for kronoterm_integration")

        existing = {
            self._strip_version(res["url"]): res
            for res in self.lovelace.resources.async_items()
        }

        for module in JSMODULES:
            url_path = f"{URL_BASE}/{module['filename']}"
            full_url = f"{url_path}?v={module['version']}"

            if url_path in existing:
                current = existing[url_path]
                if f"?v={module['version']}" in current["url"]:
                    _LOGGER.debug("Module already registered: %s", module["filename"])
                    continue

                _LOGGER.info(
                    "Updating module %s to version %s",
                    module["name"],
                    module["version"],
                )
                await self.lovelace.resources.async_update_item(
                    current["id"],
                    {"res_type": "module", "url": full_url},
                )
            else:
                _LOGGER.info("Creating new resource for %s", module["name"])
                await self.lovelace.resources.async_create_item(
                    {"res_type": "module", "url": full_url}
                )

    def _strip_version(self, url: str) -> str:
        return url.split("?")[0]
