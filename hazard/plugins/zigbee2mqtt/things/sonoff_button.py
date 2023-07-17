import asyncio
import json
import logging

from hazard.thing import register_thing
from hazard.things import Switch

LOG = logging.getLogger("hazard")


@register_thing
class SonoffButton(Switch):
    def __init__(self, hazard):
        super().__init__(hazard)

    async def dispatch_action(self, message):
        # if message["action"] == "single":
        #     await self.action("single", {"code": "button"})
        # if message["action"] == "long":
        #     await self.action("hold", {"code": "button"})
        # if message["action"] == "double":
        #     await self.action("double", {"code": "button"})

        msg = {"brightness": 40}
        msg["transition"] = 1
        client = self._hazard.find_plugin("ZigBee2MqttPlugin").client()
        await client.publish(f"zigbee2mqtt/Hobby/set", json.dumps(msg))

    async def task(self):
        print(f"start sonoff button {self._name}")
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
        return super()._features() + ["battery", "switch-hold",]
