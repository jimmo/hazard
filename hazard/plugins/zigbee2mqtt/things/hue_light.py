import asyncio
import logging
import json

from hazard.thing import register_thing
from hazard.things import Light, LEVEL_OFF, LEVEL_MIN, LEVEL_ALL, LEVEL_MAX, TEMP_COOL, TEMP_WARM

LOG = logging.getLogger("hazard")


@register_thing
class HueLight(Light):
    queue = []

    def __init__(self, hazard):
        super().__init__(hazard)
        self._temperature = TEMP_WARM

    async def publish(self, message, soft=True):
        if soft:
            message["transition"] = 0.5
        HueLight.queue.append((self._name, message,))

    async def on(self, soft=True):
        await super().on(soft)
        print("light on", self._name)
        await self.publish({"brightness": self.map_brightness()}, soft)

    async def off(self, soft=True):
        await super().off(soft)
        await self.publish({"brightness": self.map_brightness()}, soft)

    def map_temperature(self):
        return 150 + (self._temperature - TEMP_COOL) * (500 - 150) // (TEMP_WARM - TEMP_COOL)
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

    async def level(self, level=None, delta=None, soft=True, toggle=False):
        await super().level(level=level, delta=delta, soft=soft, toggle=toggle)
        await self.publish({"brightness": self.map_brightness()}, soft)

    @staticmethod
    async def send_to_group(hazard, members, message):
        if not members:
            return
        print("send to group:", members, message)
        plugin = hazard.find_plugin("ZigBee2MqttPlugin")
        group = plugin.find_group_by_members(members)
        if group:
            print("found group", group)
            await plugin.publish(f"zigbee2mqtt/{group}/set", message)
        else:
            print("individual", members, len(members))
            for name in members:
                await plugin.publish(f"zigbee2mqtt/{name}/set", message)
                await asyncio.sleep(0.1)

    @staticmethod
    async def flush(hazard):
        print("flush hue lights")
        q = HueLight.queue
        HueLight.queue = []
        last_message = {}
        members = set()
        for name, message in sorted(q, key=lambda nm: json.dumps(nm[1])):
            if message == last_message:
                members.add(name)
            else:
                if members:
                    await HueLight.send_to_group(hazard, members, last_message)
                members = set([name])
                last_message = message
        if members:
            await HueLight.send_to_group(hazard, members, last_message)
