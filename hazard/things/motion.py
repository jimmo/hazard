import async_timeout
import asyncio
import json
import logging

from hazard.thing import Thing, register_thing


LOG = logging.getLogger("hazard")


@register_thing
class MotionSensor(Thing):
    def __init__(self, hazard):
        super().__init__(hazard)
        self._active = ""
        self._inactive = ""

    def load_json(self, obj):
        super().load_json(obj)
        self._active = obj.get("active", "")
        self._inactive = obj.get("inactive", "")

    def to_json(self):
        obj = super().to_json()
        obj.update(
            {
                "json_type": "MotionSensor",
                "active": self._active,
                "inactive": self._inactive,
            }
        )
        return obj

    def _features(self):
        return super()._features() + [
            "motion",
        ]

    async def invoke(self, is_active):
        LOG.info('Invoking motion "%s/%s"', self._name, is_active)
        await self._hazard.execute(self._active if is_active else self._inactive)
