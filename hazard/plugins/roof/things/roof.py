import asyncio
import logging
import json

from hazard.thing import register_thing, Thing

LOG = logging.getLogger("hazard")


import sys
if '/home/jimmo/src/github.com/jimmo/led-roof' not in sys.path:
  sys.path.append('/home/jimmo/src/github.com/jimmo/led-roof')

import roof


@register_thing
class Roof(Thing):
    def __init__(self, hazard):
        super().__init__(hazard)
        self._rgbw = [0, 0, 0, 0]

    def to_json(self):
        obj = super().to_json()
        obj.update(
            {
                "json_type": "Roof",
                "rgbw": self._rgbw,
            }
        )
        return obj

    async def rgbw(self, rgbw=None):
        if rgbw:
            print(rgbw)
            self._rgbw = rgbw
            r, g, b, w = rgbw
            await roof.color(int(r*255), int(g*255), int(b*255), int(w*255), frames=5)

    def _features(self):
        features = super()._features() + ["roof-rgbw"]
        return features
