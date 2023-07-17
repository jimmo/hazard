import datetime
import asyncio
import logging
import math

from hazard.thing import Thing, register_thing
from hazard.things.light import Light, LEVEL_OFF, LEVEL_MIN, LEVEL_ALL, LEVEL_MAX, TEMP_COOL, TEMP_WARM

LOG = logging.getLogger("hazard")


@register_thing
class LightGroup(Light):
    def __init__(self, hazard):
        super().__init__(hazard)
        self._thing_names = []
        self._on_level = LEVEL_OFF

    async def on(self, soft=True):
        LOG.info('Setting group "%s" to ON', self._name)
        await super().on(soft=soft)
        for d in self.things():
            await d.on(soft=soft)

    def things(self):
        for t in self._thing_names:
            yield self._hazard.find_thing(t)

    async def off(self, soft=True):
        await super().off()
        for d in self.things():
            await d.off()

    async def toggle(self):
        await super().toggle()
        for d in self.things():
            if self._on:
                await d.on()
            else:
                await d.off()

    async def level(self, level=None, delta=None, soft=True, toggle=False):
        await super().level(level=level, delta=delta, soft=soft, toggle=toggle)
        LOG.info(f'Setting group "{self._name}" level to {self._level}')

        for d in self.things():
            await d.level(level=self._level, soft=soft)

    async def hue(self, hue=None, delta=None):
        await super().hue(hue, delta)
        for d in self.things():
            await d.hue(self._hue)

    async def temperature(self, temperature):
        await super().temperature(temperature)
        for d in self.things():
            await d.temperature(self._temperature)

    async def saturation(self, saturation):
        await super().saturation(saturation)
        for d in self.things():
            await d.saturation(self._saturation)

    def temperature_range(self):
        t = [d._temperature for d in self.things() if d._temperature is not None]
        if t:
            return min(t), max(t)
        else:
            return TEMP_COOL, TEMP_WARM

    def to_json(self):
        obj = super().to_json()
        obj.update(
            {
                "json_type": "Light",
                "things": sorted(self._thing_names),
            }
        )
        return obj

    def load_json(self, obj):
        super().load_json(obj)
        self._thing_names = obj.get("things", [])

    def _features(self):
        return super()._features() + ["group"]

    async def reconfigure(self):
        await super().reconfigure()
        LOG.info('Reconfigure light group "%s/%s"', self.zone(), self.name())
        if self.zone() != "Downstairs":
            return
        plugin = self._hazard.find_plugin("ZigBee2MqttPlugin")
        for d in self.things():
            LOG.info('Add "%s" to "%s"', d.name(), self.name())
            if d.zone() != "Downstairs":
                continue
            await plugin.publish(f"zigbee2mqtt/bridge/request/group/members/add", {"group": self.name(), "device": d.name()})
            await asyncio.sleep(0.5)
