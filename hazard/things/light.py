from hazard.thing import Thing, ThingGroup, register_thing

class LightBase:
  def __init__(self):
    self._on = False
    self._level = 0
    self._hue = 0
    self._temperature = 0

  async def on(self):
    self._on = True

  async def off(self):
    self._on = False

  async def toggle(self):
    self._on = not self._on

  async def level(self, level=None, delta=None):
    if level is not None:
      self._level = level
    elif delta is not None:
      self._level = min(1, max(0, self._level + delta))

  async def hue(self, hue):
    self._hue = hue

  async def temperature(self, temperature):
    self._temperature = temperature

  def to_json(self):
    return {
      'on': self._on,
      'level': self._level,
      'hue': self._hue,
      'temperature': self._temperature,
    }

@register_thing
class Light(Thing, LightBase):
  def __init__(self, hazard):
    Thing.__init__(self, hazard)
    LightBase.__init__(self)

  def _features(self):
    return super()._features() + ['light', 'light-level', 'light-temperature',]

  def to_json(self):
    json = super().to_json()
    json.update(LightBase.to_json(self))
    json.update({
      'json_type': 'Light',
    })
    return json


@register_thing
class LightGroup(ThingGroup, LightBase):
  def __init__(self, hazard):
    ThingGroup.__init__(self, hazard)
    LightBase.__init__(self)

  def _features(self):
    return super()._features() + ['light', 'light-level', 'light-temperature',]

  def to_json(self):
    json = super().to_json()
    json.update(LightBase.to_json(self))
    json.update({
      'json_type': 'Light',
    })
    return json
