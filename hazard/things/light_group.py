import datetime
import logging
import math

from hazard.thing import Thing, register_thing
from hazard.things.Light import Light, LEVEL_OFF, LEVEL_MIN, LEVEL_ALL, LEVEL_MAX

LOG = logging.getLogger("hazard")


@register_thing
class LightGroup(Light):
    def __init__(self, hazard):
        super().__init__(hazard)
        self._things = []
        self._on_level = LEVEL_OFF

    async def on(self, soft=False, time_aware=False):
        if self._on:
            if self._level > LEVEL_ALL:
                await self.level(level=LEVEL_MAX, soft=soft)
            else:
                await self.level(level=LEVEL_ALL, soft=soft)
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
                for d in self._devices:
                    await d.on(soft=soft)

    async def off(self, soft=False):
        await super().off()
        for d in self._devices:
            await d.off()

    async def toggle(self):
        await super().toggle()
        for d in self._devices:
            if self._on:
                await d.on()
            else:
                await d.off()

    async def level(self, level=None, delta=None, soft=False):
        await super().level(level=level, delta=delta, soft=soft)

        for d in self._devices:
            await d.level(level=self._level, soft=soft)

    async def hue(self, hue=None, delta=None):
        await super().hue(hue, delta)
        for d in self._devices:
            await d.hue(self._hue)

    async def temperature(self, temperature):
        await super().temperature(temperature)
        for d in self._devices:
            await d.temperature(self._temperature)

    async def saturation(self, saturation):
        await super().saturation(saturation)
        for d in self._devices:
            await d.saturation(self._saturation)

    def to_json(self):
        obj = super().to_json()
        obj.update(
            {
                "json_type": "Light",
            }
        )
        return obj

    def load_json(self, obj):
        super().load_json(obj)

    def _features(self):
        features = super()._features() + ["group"]
