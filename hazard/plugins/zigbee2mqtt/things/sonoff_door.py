import asyncio
import json
import logging

from hazard.thing import register_thing
from hazard.things import DoorSensor

LOG = logging.getLogger("hazard")


@register_thing
class SonoffDoorSensor(DoorSensor):
    def __init__(self, hazard):
        super().__init__(hazard)

    async def task(self):
        print(f"start sonoff door sensor {self._name}")
        plugin = self._hazard.find_plugin("ZigBee2MqttPlugin")
        async for message in plugin.topic_messages(f"zigbee2mqtt/{self._name}"):
            print(self._name, message.payload.decode())
            message = json.loads(message.payload)
            if "contact" in message:
                await self.invoke(not message["contact"])
            if "battery" in message:
                self._battery = message["battery"]

    async def start(self):
        self._task = asyncio.create_task(self.task())

    async def stop(self):
        self._task.cancel()
        await self._task

    def _features(self):
        return super()._features() + ["battery"]
