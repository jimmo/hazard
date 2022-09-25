import datetime
import logging
import math

from hazard.thing import Thing, register_thing

LOG = logging.getLogger('hazard')

@register_thing
class Temperature(Thing):
    def __init__(self, hazard):
        super().__init__(hazard)
        self._temperature = None
        self._humidity = None
        self._last_update = None

    def _features(self):
        features = super()._features() + ['temperature']
        if self._humidity is not None:
                features.append('humidity');
        return features

    def to_json(self):
        json = super().to_json()
        json.update({
            'json_type': 'Temperature',
            'temperature': self._temperature,
            'humidity': self._humidity,
            'last_update': self._last_update,
        })
        return json

    def load_json(self, json):
        super().load_json(json)
        self._temperature = json.get('temperature', None)
        self._humidity = json.get('humidity', None)
        self._last_update = json.get('last_update', None)
