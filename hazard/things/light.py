import datetime
import logging
import math

from hazard.thing import Thing, register_thing

LOG = logging.getLogger("hazard")

# Level:
# 0: All off
# 1: Single bulb
# 2: Half bulbs
# 3: All bulbs on lowest
# 4,5,6: Dim levels
# 7: Full brightness
LEVEL_OFF = 0
LEVEL_MIN = 1
LEVEL_ALL = 3
LEVEL_DIM = LEVEL_ALL
LEVEL_MAX = 7

# LEVEL_DIM at night, and LEVEL_MAX during the day.
LEVEL_TIME_AWARE = -1

TEMP_COOL = 0
TEMP_WARM = 7

LIGHT_LEVELS = {}
LIGHT_TEMPS = {}

def _get_all_levels():
    for n,v in globals().items():
        if n.startswith("LEVEL_"):
            LIGHT_LEVELS[n] = v
        if n.startswith("TEMP_"):
            LIGHT_TEMPS[n] = v

_get_all_levels()

def resolve_time_aware_level():
    if datetime.datetime.now().hour >= 18 or datetime.datetime.now().hour <= 6:
        return LEVEL_DIM
    else:
        return LEVEL_MAX

@register_thing
class Light(Thing):
    def __init__(self, hazard):
        super().__init__(hazard)
        self._on = False
        self._level = LEVEL_ALL
        self._hue = None
        self._temperature = None
        self._saturation = None
        self._on_level = LEVEL_ALL

    async def on(self, soft=True):
        self._on = True
        LOG.info('Setting "%s" to ON', self._name)

    async def off(self, soft=True):
        self._on = False
        LOG.info('Setting "%s" to OFF', self._name)

    async def toggle(self):
        self._on = not self._on
        LOG.info('Setting "%s" to %s', self._name, "ON" if self._on else "OFF")

    async def level(self, level=None, delta=None, soft=True, toggle=False):
        if delta is not None:
            level = self._level + delta

        if level == LEVEL_TIME_AWARE:
            level = resolve_time_aware_level()

        level = min(LEVEL_MAX, max(0, level))

        if toggle:
            if not self._on:
                self._level = level
            elif self._level == level:
                if self._level == LEVEL_DIM:
                    self._level = LEVEL_MAX
                else:
                    self._level = LEVEL_DIM
            else:
                self._level = level
        else:
            self._level = level

        self._on = self._level >= self._on_level
        LOG.info('Setting "%s" level to %d', self._name, self._level)

    async def temperature(self, temperature):
        LOG.info(f'Setting "{self._name}" temperature to {temperature}')
        self._temperature = temperature

    def to_json(self):
        obj = super().to_json()
        obj.update(
            {
                "json_type": "Light",
                "on": self._on,
                "on_level": self._on_level,
            }
        )
        if self._level is not None:
            obj.update({
                "level": self._level,
            })
        if self._hue is not None:
            obj.update({
                "hue": self._hue,
            })
        if self._temperature is not None:
            obj.update({
                "temperature": self._temperature,
            })
        if self._saturation is not None:
            obj.update({
                "saturation": self._saturation,
            })
        return obj

    def load_json(self, obj):
        super().load_json(obj)
        self._on = obj.get("on", self._on)
        self._level = obj.get("level", self._level)
        self._hue = obj.get("hue", self._hue)
        self._temperature = obj.get("temperature", self._temperature)
        self._saturation = obj.get("saturation", self._saturation)
        self._on_level = obj.get("on_level", self._on_level)

    def _features(self):
        features = super()._features() + ["light"]
        if self._level is not None:
            features.append("light-level")
        if self._hue is not None:
            features.append("light-color")
        if self._temperature is not None:
            features.append("light-temperature")
        if self._hue is not None and self._saturation is not None:
            features.append("light-saturation")
        return features
