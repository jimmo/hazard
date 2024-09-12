import datetime
import asyncio
import logging
import math

from hazard.thing import Thing, register_thing
from hazard.things.light import Light, LEVEL_OFF, LEVEL_MIN, LEVEL_ALL, LEVEL_DIM, LEVEL_MAX, LEVEL_TIME_AWARE, TEMP_COOL, TEMP_WARM, resolve_time_aware_level

LOG = logging.getLogger("hazard")


@register_thing
class LightGroup(Thing):
    def __init__(self, hazard):
        super().__init__(hazard)
        self._thing_names = []

    def things(self):
        for t in self._thing_names:
            yield self._hazard.find_thing(t)

    async def on(self, soft=True):
        LOG.info('Setting group "%s" to ON', self._name)
        for d in self.things():
            await d.on(soft=soft)

    async def off(self, soft=True):
        LOG.info('Setting group "%s" to OFF', self._name)
        for d in self.things():
            await d.off()

    async def toggle(self, soft=True):
        on = any(d._on for d in self.things())
        if on:
            await self.off(soft=soft)
        else:
            await self.on(soft=soft)

    async def level(self, level=None, delta=None, soft=True, toggle=False, tap_toggle_on=False):
        if tap_toggle_on:
            if self.any_on():
                return
            toggle = True

        if delta is not None:
            level = self.level_range()[0] + delta
        elif level == LEVEL_TIME_AWARE:
            level = resolve_time_aware_level()

        level = min(LEVEL_MAX, max(LEVEL_OFF, level))
        on = any(d._on for d in self.things())

        if toggle:
            if not on:
                pass
            elif level == self.level_range()[0]:
                if level == LEVEL_DIM:
                    level = LEVEL_MAX
                else:
                    level = LEVEL_DIM
            elif self.level_range()[0] < LEVEL_DIM:
                level = LEVEL_DIM
            else:
                pass

            LOG.info(f'Toggling group "{self._name}" level to {level}')
        else:
            LOG.info(f'Setting group "{self._name}" level to {level}')

        for d in self.things():
            if toggle or d._on or level <= LEVEL_DIM:
                await d.level(level=level, soft=soft)

        if tap_toggle_on:
            self._hazard.cancel_execute()

    async def hue(self, hue=None, delta=None):
        for d in self.things():
            await d.hue(hue)

    async def temperature(self, temperature):
        for d in self.things():
            await d.temperature(temperature)

    async def saturation(self, saturation):
        for d in self.things():
            await d.saturation(saturation)

    def any_on(self):
        return any(d._on for d in self.things())

    def level_range(self):
        t = [d._level for d in self.things() if d._level is not None and d._on]
        if t:
            return min(t), max(t)
        else:
            return LEVEL_OFF, LEVEL_OFF

    def temperature_range(self):
        t = [d._temperature for d in self.things() if d._temperature is not None and d._on]
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
                "on": self.any_on(),
                "level": self.level_range()[0],
                "temperature": self.temperature_range()[1],
            }
        )
        return obj

    def load_json(self, obj):
        super().load_json(obj)
        self._thing_names = obj.get("things", [])

    def _features(self):
        f = set(("group",))
        for d in self.things():
            f.update(d._features())
        return list(f)

    async def reconfigure(self):
        await super().reconfigure()
        LOG.info('Reconfigure light group "%s/%s"', self.zone(), self.name())
        plugin = self._hazard.find_plugin("ZigBee2MqttPlugin")
        for d in self.things():
            LOG.info('Add "%s" to "%s"', d.name(), self.name())
            await plugin.publish(f"zigbee2mqtt/bridge/request/group/members/add", {"group": self.name(), "device": d.name()})
            await asyncio.sleep(0.5)
