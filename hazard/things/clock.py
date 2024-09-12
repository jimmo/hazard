from hazard.thing import Thing, register_thing

import asyncio
import logging

LOG = logging.getLogger("hazard")


@register_thing
class Clock(Thing):
    def __init__(self, hazard):
        super().__init__(hazard)
        self._name = "Clock"
        self._interval = 10
        self._code = ""

    async def start(self):
        self._task = asyncio.create_task(self.task())

    async def stop(self):
        self._task.cancel()
        await self._task

    def _features(self):
        return super()._features() + ["clock"]

    def load_json(self, json):
        super().load_json(json)
        self._interval = json.get("interval", 10)
        self._code = json.get("code", "")

    def to_json(self):
        json = super().to_json()
        json.update(
            {
                "interval": self._interval,
                "code": self._code,
            }
        )
        return json

    async def task(self):
        while True:
            await asyncio.sleep(self._interval)
            # LOG.info('Clock tick')
            await self._hazard.execute(self._code)
            self._hazard.save()

