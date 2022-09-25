import logging

from hazard.thing import register_thing
from hazard.things import Switch

LOG = logging.getLogger('hazard')


@register_thing
class SonoffButton(Switch):
    def __init__(self, hazard):
        super().__init__(hazard)

    def to_json(self):
        json = super().to_json()
        json.update({
        })
        return json

    def load_json(self, json):
        super().load_json(json)
