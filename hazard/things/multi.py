import async_timeout
import asyncio
import json
import logging

from hazard.thing import Thing, register_thing


LOG = logging.getLogger("hazard")


@register_thing
class MultiSensor(Thing):
    def __init__(self, hazard):
        super().__init__(hazard)
        self._open = ""
        self._close = ""

    def load_json(self, obj):
        super().load_json(obj)
        self._open = obj.get("open", "")
        self._close = obj.get("close", "")

    def to_json(self):
        obj = super().to_json()
        obj.update(
            {
                "json_type": "MultiSensor",
                "open": self._open,
                "close": self._close,
            }
        )
        return obj

    def _features(self):
        return super()._features() + [
            "multi",
        ]

    async def invoke_openclose(self, is_open):
        LOG.info('Invoking multi open/close "%s/%s"', self._name, is_open)
        await self._hazard.execute(self._open if is_open else self._close)
