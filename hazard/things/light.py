from hazard.thing import Thing, ThingGroup, register_thing

class LightBase:
  def __init__(self):
    self._level = False
    self._color = False
    self._temperature = False

  async def on(self):
    pass

  async def off(self):
    pass

  async def toggle(self):
    print('toggle', self._name)

  async def level(self, level):
    print('level', self._name, level)

  async def hue(self, hue):
    pass

  async def temperature(self, temperature):
    print('temperature', self._name, temperature)


@register_thing
class Light(Thing, LightBase):
  def __init__(self, hazard):
    Thing.__init__(self, hazard)
    LightBase.__init__(self)

  def _features(self):
    return super()._features() + ['light', 'light-level', 'light-temperature',]


@register_thing
class LightGroup(ThingGroup, LightBase):
  def __init__(self, hazard):
    ThingGroup.__init__(self, hazard)
    LightBase.__init__(self)

  def _features(self):
    return super()._features() + ['light', 'light-level', 'light-temperature',]
