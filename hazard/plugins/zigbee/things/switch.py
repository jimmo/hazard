from hazard.thing import register_thing
from hazard.things import Switch, SwitchButton


class ZigBeeSwitchButton(SwitchButton):
  def __init__(self, switch):
    super().__init__(switch)
    self._endpoint = 1

  async def _on_zcl(self, cluster_name, command_type, command_name, **kwargs):
    if cluster_name == 'onoff' and command_name == 'toggle':
      await self.action_tap()

  def to_json(self):
    json = super().to_json()
    json.update({
      'endpoint': self._endpoint,
    })
    return json

  def load_json(self, json):
    super().load_json(json)
    self._endpoint = json['endpoint']


@register_thing
class ZigBeeSwitch(Switch):
  def __init__(self, hazard):
    super().__init__(hazard)
    self._device = None

  async def _on_zcl(self, source_endpoint, dest_endpoint, cluster_name, command_type, command_name, **kwargs):
    #print('switch', source_endpoint, dest_endpoint, cluster_name, command_type, command_name, **kwargs)
    for btn in self._buttons:
      if source_endpoint == btn._endpoint:
        await btn._on_zcl(cluster_name, command_type, command_name, **kwargs)

  async def create_from_device(self, device):
    self._device = device
    self._device.register_zcl(self._on_zcl)
    self._name = device._name

    active_eps = await device.zdo('active_ep', addr16=device._addr16)
    for endpoint in active_eps['active_eps']:
      desc = await device.zdo('simple_desc', addr16=device._addr16, endpoint=endpoint)
      desc = desc['simple_descriptors'][0]
      btn = self._create_button()
      btn._endpoint = desc['endpoint']
      self._buttons.append(btn)

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
