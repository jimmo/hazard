from hazard.thing import register_thing
from hazard.things import Light

import zcl.spec

@register_thing
class ZigBeeLight(Light):
  def __init__(self, hazard):
    super().__init__(hazard)
    self._device = None
    self._endpoint = None

  async def on(self):
    if not self._device:
      return
    await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'onoff', 'on', timeout=5)

  async def off(self):
    if not self._device:
      return
    await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'onoff', 'off', timeout=5)

  async def toggle(self):
    if not self._device:
      return
    await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'onoff', 'toggle', timeout=5)

  async def level(self, level):
    if not self._device:
      return
    await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'level_control', 'move_to_level', timeout=5, level=int(level*255), time=20)

  async def hue(self, hue):
    if not self._device:
      return
    await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'color', 'move_to_hue', timeout=5, hue=int(hue*255), dir=0, time=20)

  async def temperature(self, temperature):
    if not self._device:
      return
    await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'onoff', 'on', timeout=5, mireds=0, time=10)

  def to_json(self):
    json = super().to_json()
    json.update({
      'device': self._device.addr64hex() if self._device else None,
      'endpoint': self._endpoint,
    })
    return json

  def from_json(self, json):
    super().from_json(json)
    self._device = self._hazard.find_plugin(ZigBeePlugin).network().find_device(json['device'])
    self._endpoint = json['endpoint']
