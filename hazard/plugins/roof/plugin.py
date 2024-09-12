import json

from hazard.plugin import HazardPlugin, register_plugin

import hazard.plugins.roof.things

@register_plugin
class RoofPlugin(HazardPlugin):
    def __init__(self, hazard):
        super().__init__(hazard)

    def load_json(self, json):
        super().load_json(json)

    def to_json(self):
        json = super().to_json()
        return json

    async def start(self):
        print("Roof plugin start")

    async def stop(self):
        print("Roof plugin stop")

