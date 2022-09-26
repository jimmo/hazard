import asyncio
import json
import logging

from hazard.thing import register_thing
from hazard.things import Switch

LOG = logging.getLogger("hazard")


@register_thing
class SmartenItSwitch(Switch):
    def __init__(self, hazard):
        super().__init__(hazard)

    async def dispatch_action(self, message):
        if message["action"] == "toggle_left":
            await self.action("invoke", {"code": "left"})
        if message["action"] == "toggle_center":
            await self.action("invoke", {"code": "center"})
        if message["action"] == "toggle_right":
            await self.action("invoke", {"code": "right"})

    async def task(self):
        print(f"start smartenit switch {self._name}")
        client = self._hazard.find_plugin("ZigBee2MqttPlugin").client()
        async with client.filtered_messages(f"zigbee2mqtt/{self._name}") as messages:
            async for message in messages:
                print(self._name, message.payload.decode())
                message = json.loads(message.payload)
                if "action" in message:
                    await self.dispatch_action(message)
                if "battery_low" in message:
                    self._battery = 5 if message["battery_low"] else 100

    async def start(self):
        self._task = asyncio.create_task(self.task())

    async def stop(self):
        self._task.cancel()
        await self._task

    def _features(self):
        return super()._features() + ["battery", "switch-tap"]
