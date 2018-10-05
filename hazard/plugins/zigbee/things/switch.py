import json

from hazard.thing import register_thing
from hazard.things import Switch, SwitchButton


@register_thing
class ZigBeeSwitch(Switch):
  def __init__(self, hazard):
    super().__init__(hazard)
    self._device = None

  async def _on_zcl(self, source_endpoint, dest_endpoint, cluster_name, command_type, command_name, **kwargs):
    print('switch', source_endpoint, dest_endpoint, cluster_name, command_type, command_name, repr(kwargs))
    code = {
      'endpoint': source_endpoint,
      'cluster': cluster_name,
      'command': command_name,
      'args': kwargs,
    }
    await self.get_button(code).invoke()

  async def create_from_device(self, device):
    self._device = device
    self._device.register_zcl(self._on_zcl)
    self._name = device._name

  def to_json(self):
    json = super().to_json()
    json.update({
      'device': self._device.addr64hex() if self._device else None,
    })
    return json

  def load_json(self, json):
    super().load_json(json)
    self._device = self._hazard.find_plugin('ZigBeePlugin').network().find_device(json['device'])
    self._device.register_zcl(self._on_zcl)

  def _create_button(self):
    return ZigBeeSwitchButton(self)
