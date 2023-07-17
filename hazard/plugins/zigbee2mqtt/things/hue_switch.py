import asyncio
import json
import logging

from hazard.thing import register_thing
from hazard.things import Switch

LOG = logging.getLogger("hazard")


@register_thing
class HueSwitch(Switch):
    def __init__(self, hazard):
        super().__init__(hazard)
        self._task = None

    async def dispatch_action(self, message):
        if message["action"] == "on_press":
            await self.action("invoke", {"code": "on"})
        if message["action"] == "on_hold":
            await self.action("hold", {"code": "on"})
        if message["action"] == "up_press":
            await self.action("invoke", {"code": "up"})
        if message["action"] == "up_hold":
            await self.action("hold", {"code": "up"})
        if message["action"] == "down_press":
            await self.action("invoke", {"code": "down"})
        if message["action"] == "down_hold":
            await self.action("hold", {"code": "down"})
        if message["action"] == "off_press":
            await self.action("invoke", {"code": "off"})
        if message["action"] == "off_hold":
            await self.action("hold", {"code": "off"})

    async def task(self):
        print(f"start hue switch {self._name}")
        plugin = self._hazard.find_plugin("ZigBee2MqttPlugin")
        async for message in plugin.topic_messages(f"zigbee2mqtt/{self._name}"):
            print(self._name, message.payload.decode())
            message = json.loads(message.payload)
            if "action" in message:
                await self.dispatch_action(message)
            if "battery" in message:
                self._battery = message["battery"]

    async def start(self):
        self._task = asyncio.create_task(self.task())

    async def stop(self):
        self._task.cancel()
        await self._task

    def _features(self):
        return super()._features() + ["battery", "switch-hold", "switch-tap"]
