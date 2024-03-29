import logging

from hazard.thing import register_thing
from hazard.things import Light

LOG = logging.getLogger("hazard")


@register_thing
class LifxLight(Light):
    def __init__(self, hazard):
        super().__init__(hazard)

    def to_json(self):
        json = super().to_json()
        json.update({})
        return json

    def load_json(self, json):
        super().load_json(json)
