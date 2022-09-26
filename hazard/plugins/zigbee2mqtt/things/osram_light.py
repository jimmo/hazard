import json
import logging

from hazard.thing import register_thing
from hazard.things import Light, LEVEL_OFF, LEVEL_MIN, LEVEL_ALL, LEVEL_MAX, TEMP_COOL, TEMP_WARM

LOG = logging.getLogger("hazard")


@register_thing
class OsramLight(Light):
    def __init__(self, hazard):
        super().__init__(hazard)
        self._temperature = TEMP_WARM

    async def publish(self, msg, soft=False):
        if soft:
            msg["transition"] = 1
        client = self._hazard.find_plugin("ZigBee2MqttPlugin").client()
        await client.publish(f"zigbee2mqtt/{self._name}/set", json.dumps(msg))

    async def on(self, soft=False):
        await super().on(soft)
        await self.publish({"state": "ON"}, soft)

    async def off(self, soft=False):
        await super().off(soft)
        await self.publish({"state": "OFF"}, soft)

    def map_temperature(self):
        return 153 + (self._temperature - TEMP_COOL) * (370 - 153) // (TEMP_WARM - TEMP_COOL)
        # 153 and 370
        #2400 4200

    async def temperature(self, temperature):
        await super().temperature(temperature)
        await self.publish({"color_temp": self.map_temperature()})

    def map_brightness(self):
        if not self._on or self._level == 0:
            return 0
        if self._level <= LEVEL_ALL:
            return 1
        return 1 + (self._level - LEVEL_ALL) * 253 // (LEVEL_MAX - LEVEL_ALL)

    async def level(self, level=None, delta=None, soft=False):
        await super().level(level=level, delta=delta, soft=soft)
        await self.publish({"brightness": self.map_brightness()}, soft)
