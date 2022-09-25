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
LEVEL_MAX = 7


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

    async def on(self, soft=False):
        self._on = True
        LOG.info('Setting "%s" to ON', self._name)

    async def off(self, soft=False):
        self._on = False
        LOG.info('Setting "%s" to OFF', self._name)

    async def toggle(self):
        self._on = not self._on
        LOG.info('Setting "%s" to %s', self._name, "ON" if self._on else "OFF")

    async def level(self, level=None, delta=None, soft=False):
        if delta is not None:
            level = self._level + delta

        self._level = min(LEVEL_MAX, max(0, level))
        self._on = self._level >= self._on_level
        LOG.info('Setting "%s" level to %d', self._name, self._level)

    # async def hue(self, hue=None, delta=None):
    #     if not self._on:
    #         return
    #     if hue is not None:
    #         self._hue = min(1, max(0, hue))
    #     elif delta is not None:
    #         if self._hue is None:
    #             self._hue = 0
    #         self._hue += delta
    #         self._hue -= math.floor(self._hue)

    # async def temperature(self, temperature):
    #     if not self._on:
    #         return
    #     self._temperature = temperature

    # async def saturation(self, saturation):
    #     if not self._on:
    #         return
    #     self._saturation = saturation

    def to_json(self):
        obj = super().to_json()
        obj.update(
            {
                "json_type": "Light",
                "on": self._on,
                "level": self._level,
                "hue": self._hue,
                "temperature": self._temperature,
                "saturation": self._saturation,
                "on_level": self._on_level,
            }
        )
        return obj

    def load_json(self, obj):
        super().load_json(obj)
        self._on = obj.get("on", False)
        self._level = obj.get("level", LEVEL_ALL)
        self._hue = obj.get("hue", None)
        self._temperature = obj.get("temperature", None)
        self._saturation = obj.get("saturation", None)
        self._on_level = obj.get("on_level", LEVEL_ALL)

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
