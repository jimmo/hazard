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

    def to_json(self):
        json = super().to_json()
        json.update({})
        return json

    def load_json(self, json):
        super().load_json(json)

    async def task(self):
        print(f"start hue switch {self._name}")
        client = self._hazard.find_plugin("ZigBee2MqttPlugin").client()
        async with client.filtered_messages(f"zigbee2mqtt/{self._name}") as messages:
            async for message in messages:
                print(self._name, message.payload.decode())
                message = json.loads(message.payload)
                b = self._hazard.find_thing("Hobby 1")
                if message["action"] == "on_press":
                    await b.on(soft=True)
                if message["action"] == "off_press":
                    await b.off(soft=True)

    async def start(self):
        self._task = asyncio.create_task(self.task())

    async def stop(self):
        self._task.cancel()
        await self._task
