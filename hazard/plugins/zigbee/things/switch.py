from hazard.thing import register_thing
from hazard.things import Light

@register_thing
class ZigBeeSwitch(Light):
  def __init__(self, hazard):
    super().__init__(self, hazard)
