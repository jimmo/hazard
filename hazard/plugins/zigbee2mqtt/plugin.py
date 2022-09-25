from hazard.plugin import HazardPlugin, register_plugin

import hazard.plugins.zigbee2mqtt.things

import asyncio_mqtt
import asyncio


@register_plugin
class ZigBee2MqttPlugin(HazardPlugin):
    def __init__(self, hazard):
        super().__init__(hazard)
        self._task = None
        self._broker = "localhost"
        self._client = None

    def load_json(self, json):
        super().load_json(json)
        self._broker = json.get("broker", "localhost")

    def to_json(self):
        json = super().to_json()
        json.update({"broker": self._broker})
        return json

    async def start(self):
        print("Connecting to mqtt broker")
        self._client = asyncio_mqtt.Client("localhost")
        await self._client.connect()
        await self._client.subscribe("zigbee2mqtt/#")

    def client(self):
        return self._client
