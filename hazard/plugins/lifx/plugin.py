import aiohttp.web

from hazard.plugin import HazardPlugin, register_plugin

import hazard.plugins.lifx.things


@register_plugin
class LifxPlugin(HazardPlugin):
    def __init__(self, hazard):
        super().__init__(hazard)

    async def start(self):
        pass
