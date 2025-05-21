"""Various config flows."""

from homeassistant import config_entries

from .const import DOMAIN


class KronotermConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for using Kronoterm cloud."""

    async def async_step_user(self, info: object) -> config_entries.ConfigFlowResult:
        """Config flow."""
        return self.async_create_entry(title="Kronoterm entry", data={})
