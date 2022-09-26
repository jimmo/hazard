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

    async def on(self, soft=False, time_aware=False):
        LOG.info('Setting group "%s" to ON', self._name)
        if self._on:
            if self._level > LEVEL_ALL:
                await self.level(level=LEVEL_ALL, soft=soft)
            else:
                await self.level(level=LEVEL_MAX, soft=soft)
        else:
            if time_aware and (
                datetime.datetime.now().hour >= 18 or datetime.datetime.now().hour <= 6
            ):
                await self.level(level=LEVEL_ALL, soft=soft)
            elif time_aware and (
                datetime.datetime.now().hour >= 7 or datetime.datetime.now().hour <= 11
            ):
                await self.level(level=LEVEL_MAX, soft=soft)
            else:
                await super().on(soft=soft)
                for d in self.things():
                    await d.on(soft=soft)
                    await asyncio.sleep(0.1)

    def things(self):
        for t in self._thing_names:
            yield self._hazard.find_thing(t)

    async def off(self, soft=False):
        await super().off()
        for d in self.things():
            await d.off()
            await asyncio.sleep(0.1)

    async def toggle(self):
        await super().toggle()
        for d in self.things():
            if self._on:
                await d.on()
            else:
                await d.off()
            await asyncio.sleep(0.1)

    async def level(self, level=None, delta=None, soft=False):
        await super().level(level=level, delta=delta, soft=soft)
        LOG.info(f'Setting group "{self._name}" level to {self._level}')

        for d in self.things():
            await d.level(level=self._level, soft=soft)
            await asyncio.sleep(0.1)

    async def hue(self, hue=None, delta=None):
        await super().hue(hue, delta)
        for d in self.things():
            await d.hue(self._hue)
            await asyncio.sleep(0.1)

    async def temperature(self, temperature):
        await super().temperature(temperature)
        for d in self.things():
            await d.temperature(self._temperature)
            await asyncio.sleep(0.1)

    async def saturation(self, saturation):
        await super().saturation(saturation)
        for d in self.things():
            await d.saturation(self._saturation)
            await asyncio.sleep(0.1)

    def to_json(self):
        obj = super().to_json()
        obj.update(
            {
                "json_type": "Light",
                "things": self._thing_names,
            }
        )
        return obj

    def load_json(self, obj):
        super().load_json(obj)
        self._thing_names = obj.get("things", [])

    def _features(self):
        return super()._features() + ["group"]
