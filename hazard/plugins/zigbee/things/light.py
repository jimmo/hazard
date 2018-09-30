from hazard.thing import register_thing
from hazard.things import Light, LightGroup

import zcl.spec

import random

TRANSITION_TIME = 0


@register_thing
class ZigBeeLight(Light):
  def __init__(self, hazard):
    super().__init__(hazard)
    self._device = None
    self._endpoint = None

  async def create_from_device(self, device):
    self._device = device
    self._device.register_zcl(self._on_zcl)
    self._name = device._name

    active_eps = await device.zdo('active_ep', addr16=device._addr16)
    for endpoint in active_eps['active_eps']:
      desc = await device.zdo('simple_desc', addr16=device._addr16, endpoint=endpoint)
      desc = desc['simple_descriptors'][0]
      self._endpoint = desc['endpoint']
      break
    
  async def _on_zcl(self, source_endpoint, dest_endpoint, cluster_name, command_type, command_name, **kwargs):
    print(repr(kwargs))
    if command_name == 'report_attributes':
      print(self._name, cluster_name, command_type, command_name, [a['attribute'] for a in kwargs['attributes']])
    if command_type == zcl.spec.ZclCommandType.PROFILE and command_name == 'report_attributes':
      if cluster_name == 'onoff':
        self._on = bool(kwargs['attributes'][0]['value'])
      elif cluster_name == 'level_control':
        print(kwargs['attributes'][0]['value'])
        self._level = (kwargs['attributes'][0]['value'] - 1) / 253
      elif cluster_name == 'color':
        if kwargs['attributes'][0]['attribute'] == 7:
          mireds = kwargs['attributes'][0]['value']
          self._temperature = int(1e6 / mireds)
        elif kwargs['attributes'][0]['attribute'] == 1:
          self._saturation = kwargs['attributes'][0]['value'] / 255
        elif kwargs['attributes'][0]['attribute'] == 0:
          self._hue = kwargs['attributes'][0]['value'] / 255
      else:
        print('light attribute', source_endpoint, dest_endpoint, cluster_name, command_type, command_name, repr(kwargs))


  async def on(self):
    if not self._device:
      return
    await super().on()
    await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'onoff', 'on', timeout=5)

  async def off(self):
    if not self._device:
      return
    await super().off()
    #await self.configure_reporting()
    await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'onoff', 'off', timeout=5)

  async def toggle(self):
    if not self._device:
      return
    await super().toggle()
    await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'onoff', 'toggle', timeout=5)

  async def level(self, level=None, delta=None):
    if not self._device:
      return
    await super().level(level, delta)
    print('new thing level', self._level)
    await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'level_control', 'move_to_level', timeout=5, level=int(self._level*253) + 1, time=TRANSITION_TIME)

  async def hue(self, hue):
    if not self._device:
      return
    await super().hue(hue)
    await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'color', 'move_to_hue', timeout=5, hue=int(hue*255), dir=0, time=TRANSITION_TIME)

  async def saturation(self, saturation):
    if not self._device:
      return
    await super().saturation(hue)
    await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'color', 'move_to_saturation', timeout=5, saturation=int(saturation*255), dir=0, time=TRANSITION_TIME)

  async def temperature(self, temperature):
    if not self._device:
      return
    await super().temperature(temperature)
    mireds = int(1e6 / temperature)
    await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'color', 'move_to_color_temperature', timeout=5, mireds=mireds, time=TRANSITION_TIME)

  async def configure_reporting(self):
    await self._device.zcl_profile(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'level_control', 'configure_reporting', timeout=5, configs=[
      {
        'attribute': 0,
        'datatype': 'uint8',
        'minimum': 5,
        'maximum': 0,
        'delta': 10,
      }
    ])
    await self._device.zcl_profile(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'onoff', 'configure_reporting', timeout=5, configs=[
      {
        'attribute': 0,
        'datatype': 'bool',
        'minimum': 5,
        'maximum': 240 + random.randint(0, 15),
      }
    ])

  async def reconfigure(self):
    print('Reconfigure', self.name())
    await self.configure_reporting()
    
  def to_json(self):
    json = super().to_json()
    json.update({
      'device': self._device.addr64hex() if self._device else None,
      'endpoint': self._endpoint,
    })
    return json

  def load_json(self, json):
    super().load_json(json)
    self._device = self._hazard.find_plugin('ZigBeePlugin').network().find_device(json['device'])
    self._device.register_zcl(self._on_zcl)
    self._endpoint = json['endpoint']



@register_thing
class ZigBeeLightGroup(LightGroup):
  def __init__(self, hazard):
    super().__init__(hazard)
    self._group = None
    self._endpoint = None

  async def create_from_group(self, group):
    self._group = group
    self._name = group._name

    # TODO: Query endpoints from group devices.
    self._endpoint = 3

  async def on(self):
    if not self._group:
      return
    await super().on()
    await self._group.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'onoff', 'on', timeout=5)

  async def off(self):
    if not self._group:
      return
    await super().off()
    await self._group.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'onoff', 'off', timeout=5)

  async def toggle(self):
    if not self._group:
      return
    await super().toggle()
    await self._group.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'onoff', 'toggle', timeout=5)

  async def level(self, level=None, delta=None):
    if not self._group:
      return
    await super().level(level, delta)
    print('new group level', self._level)
    await self._group.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'level_control', 'move_to_level', timeout=5, level=int(self._level*253) + 1, time=TRANSITION_TIME)

  async def hue(self, hue):
    if not self._group:
      return
    await super().hue(hue)
    await self._group.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'color', 'move_to_hue', timeout=5, hue=int(hue*255), dir=0, time=TRANSITION_TIME)

  async def temperature(self, temperature):
    if not self._group:
      return
    await super().temperature(temperature)
    mireds = int(1e6 / temperature)
    await self._group.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'color', 'move_to_color_temperature', timeout=5, mireds=mireds, time=TRANSITION_TIME)

  def to_json(self):
    json = super().to_json()
    json.update({
      'group': self._group._addr16 if self._group else None,
      'endpoint': self._endpoint,
    })
    return json

  def load_json(self, json):
    super().load_json(json)
    self._group = self._hazard.find_plugin('ZigBeePlugin').network().find_group(json['group'])
    self._endpoint = json['endpoint']
