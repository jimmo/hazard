import datetime
import logging
import math

from hazard.thing import Thing, register_thing

LOG = logging.getLogger('hazard')

LOW_LEVEL = 0.1

@register_thing
class Light(Thing):
  def __init__(self, hazard):
    super().__init__(hazard)
    self._on = False
    self._level = 0.6
    self._hue = None
    self._temperature = 2400
    self._saturation = 1
    self._priority = 0

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
      self._level = min(1, max(LOW_LEVEL, level))
    elif delta is not None:
      if self._level is None:
        self._level = LOW_LEVEL
      if delta < 0 and self._level > LOW_LEVEL:
        self._level = min(1, max(LOW_LEVEL, self._level + delta))
      else:
        self._level = min(1, max(LOW_LEVEL, self._level + delta))
    self._on = self._level > 0
    LOG.info('Setting "%s" level to %f', self._name, self._level)

  async def hue(self, hue=None, delta=None):
    if not self._on:
      return
    if hue is not None:
      self._hue = min(1, max(0, hue))
    elif delta is not None:
      if self._hue is None:
        self._hue = 0
      self._hue += delta
      self._hue -= math.floor(self._hue)

  async def temperature(self, temperature):
    if not self._on:
      return
    self._temperature = temperature

  async def saturation(self, saturation):
    if not self._on:
      return
    self._saturation = saturation

  async def on_level(self, soft=False, time_aware=False):
    if self._on:
      if self._level < 0.5:
        await self.level(level=1, onoff=True, soft=soft)
      else:
        await self.level(level=LOW_LEVEL, onoff=True, soft=soft)
    else:
      if time_aware and (datetime.datetime.now().hour >= 18 or datetime.datetime.now().hour <= 6):
        await self.level(level=LOW_LEVEL, onoff=True, soft=soft)
      elif time_aware and (datetime.datetime.now().hour >= 7 or datetime.datetime.now().hour <= 11):
        await self.level(level=1, onoff=True, soft=soft)
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
      'priority': self._priority,
    })
    return obj

  def _get_json(self, obj, n):
    if n in obj and obj[n] is not None:
      return obj[n]
    return getattr(self, '_' + n)

  def load_json(self, obj):
    super().load_json(obj)
    self._on = self._get_json(obj, 'on')
    self._level = self._get_json(obj, 'on')
    self._hue = self._get_json(obj, 'hue')
    self._temperature = self._get_json(obj, 'temperature')
    self._saturation = self._get_json(obj, 'saturation')
    self._priority = self._get_json(obj, 'priority')

  def _features(self):
    features = super()._features() + ['light'];
    if self._level is not None:
      features.append('light-level')
    if self._hue is not None:
      features.append('light-color')
    if self._temperature is not None:
      features.append('light-temperature')
    if self._hue is not None and self._saturation is not None:
      features.append('light-saturation')
    return features
