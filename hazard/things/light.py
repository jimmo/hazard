import datetime
import logging

from hazard.thing import Thing, register_thing

LOG = logging.getLogger('thing')

@register_thing
class Light(Thing):
  def __init__(self, hazard):
    super().__init__(hazard)
    self._on = False
    self._level = 0.6
    self._hue = None
    self._temperature = None
    self._saturation = None

  async def on(self, soft=False):
    self._on = True
    LOG.info('Setting "%s" to ON', self._name)

  async def off(self, soft=False):
    self._on = False
    LOG.info('Setting "%s" to OFF', self._name)

  async def toggle(self):
    self._on = not self._on
    LOG.info('Setting "%s" to %s', self._name, 'ON' if self._on else 'OFF')

  async def level(self, level=None, delta=None, onoff=False, soft=False):
    if level is not None:
      self._level = min(1, max(0, level))
    elif delta is not None:
      if self._level is None:
        self._level = 0.5
      if delta < 0 and self._level > 0.05:
        self._level = min(1, max(0.05, self._level + delta))
      else:
        self._level = min(1, max(0, self._level + delta))
    self._on = self._level > 0
    LOG.info('Setting "%s" level to %f', self._name, self._level)

  async def hue(self, hue):
    self._hue = hue

  async def temperature(self, temperature):
    self._temperature = temperature

  async def saturation(self, saturation):
    self._saturation = saturation

  async def on_level(self, soft=False, time_aware=False):
    if self._on:
      if self._level < 0.5:
        await self.level(level=1, onoff=True, soft=soft)
      else:
        await self.level(level=0.05, onoff=True, soft=soft)
    else:
      if time_aware and datetime.datetime.now().hour >= 18:
        await self.level(level=0.05, onoff=True, soft=soft)
      else:
        await self.on(soft=soft)

  def to_json(self):
    obj = super().to_json()
    obj.update({
      'json_type': 'Light',
      'on': self._on,
      'level': self._level,
      'hue': self._hue,
      'temperature': self._temperature,
      'saturation': self._saturation,
    })
    return obj

  def load_json(self, obj):
    super().load_json(obj)
    self._on = obj.get('on', False)
    self._level = obj.get('on', 0.6)
    self._hue = obj.get('on', None)
    self._temperature = obj.get('on', None)
    self._saturation = obj.get('saturation', None)

  def _features(self):
    features = super()._features() + ['light'];
    if self._level is not None:
      features.append('light-level')
    if self._hue is not None:
      features.append('light-color')
    if self._temperature is not None:
      features.append('light-temperature')
    if self._saturation is not None:
      features.append('light-saturation')
    return features
