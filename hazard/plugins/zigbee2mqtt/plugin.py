import json

from hazard.plugin import HazardPlugin, register_plugin

import hazard.plugins.zigbee2mqtt.things

import aiomqtt
import asyncio


@register_plugin
class ZigBee2MqttPlugin(HazardPlugin):
    def __init__(self, hazard):
        super().__init__(hazard)
        self._devices_task = None
        self._groups_task = None
        self._broker = "localhost"
        self._client = None
        self._devices_by_addr = {}
        self._groups = []
        self._group_members = {}

    def load_json(self, json):
        super().load_json(json)
        self._broker = json.get("broker", "localhost")

    def to_json(self):
        json = super().to_json()
        json.update({"broker": self._broker})
        return json

    async def publish(self, topic, message):
        await self._client.publish(topic, json.dumps(message))

    def update_group_membership(self):
        if not self._devices_by_addr or not self._groups:
            return
        self._group_members = {}
        for g in self._groups:
            n = g["friendly_name"]
            self._group_members[n] = set()
            for m in g["members"]:
                addr = m["ieee_address"]
                if addr in self._devices_by_addr:
                    self._group_members[n].add(self._devices_by_addr[addr])

    def find_group_by_members(self, members):
        for n, m in self._group_members.items():
            if m == members:
                return n
        return None

    async def topic_messages(self, topic: str):
        async with self._client.messages() as messages:
            await self._client.subscribe(topic + "/#")
            async for message in messages:
                if message.topic.matches(topic):
                    yield message

    async def devices_task(self):
        print(f"start devices task")
        async for message in self.topic_messages(f"zigbee2mqtt/bridge/devices"):
            devices = json.loads(message.payload)
            self._devices_by_addr = {d["ieee_address"]: d["friendly_name"] for d in devices}
            self.update_group_membership()
            print("updated devices")

    async def groups_task(self):
        print(f"start groups task")
        async for message in self.topic_messages(f"zigbee2mqtt/bridge/groups"):
            self._groups = json.loads(message.payload)
            self.update_group_membership()
            print("updated groups")

    async def start(self):
        print("Connecting to mqtt broker")
        self._client = aiomqtt.Client(self._broker)
        await self._client.connect()
        self._devices_task = asyncio.create_task(self.devices_task())
        self._groups_task = asyncio.create_task(self.groups_task())

    async def stop(self):
        self._devices_task.cancel()
        self._groups_task.cancel()
        await asyncio.gather(self._devices_task, self._groups_task)

    def client(self):
        return self._client
