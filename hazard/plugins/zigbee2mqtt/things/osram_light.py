import json
import logging

from hazard.thing import register_thing
from hazard.things import Light

LOG = logging.getLogger("hazard")


@register_thing
class OsramLight(Light):
    def __init__(self, hazard):
        super().__init__(hazard)

    def to_json(self):
        json = super().to_json()
        json.update({})
        return json

    def load_json(self, json):
        super().load_json(json)

    async def publish(self, msg):
        client = self._hazard.find_plugin("ZigBee2MqttPlugin").client()
        await client.publish(f"zigbee2mqtt/{self._name}/set", json.dumps(msg))

    async def on(self, soft=False):
        await super().on(soft)
        msg = {"state": "ON"}
        if soft:
            msg["transition"] = 1
        await self.publish(msg)

    async def off(self, soft=False):
        await super().off(soft)
        msg = {"state": "OFF"}
        if soft:
            msg["transition"] = 1
        await self.publish(msg)

    async def level(self, level=None, delta=None, soft=False):
        await super().level(soft)
        # TODO
