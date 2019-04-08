import logging

from hazard.thing import register_thing
from hazard.things import Light

import zcl.spec

import random

TRANSITION_TIME_HARD = 0
TRANSITION_TIME_SOFT = 2

LOG = logging.getLogger('zigbee')


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
    if command_type == zcl.spec.ZclCommandType.PROFILE and command_name == 'report_attributes':
      if cluster_name == 'onoff':
        self._on = bool(kwargs['attributes'][0]['value'])
        LOG.info('Update "%s" onoff=%s', self._name, self._on)
      elif cluster_name == 'level_control':
        self._level = (kwargs['attributes'][0]['value'] - 1) / 253
        LOG.info('Update "%s" level=%f', self._name, self._level)
      elif cluster_name == 'color':
        if kwargs['attributes'][0]['attribute'] == 7:
          mireds = kwargs['attributes'][0]['value']
          self._temperature = int(1e6 / mireds)
          LOG.info('Update "%s" temperature=%f', self._name, self._temperature)
        elif kwargs['attributes'][0]['attribute'] == 1:
          self._saturation = kwargs['attributes'][0]['value'] / 255
          LOG.info('Update "%s" saturation=%f', self._name, self._saturation)
        elif kwargs['attributes'][0]['attribute'] == 0:
          self._hue = kwargs['attributes'][0]['value'] / 255
          LOG.info('Update "%s" hue=%f', self._name, self._hue)
      else:
        LOG.error('unknown light attribute', source_endpoint, dest_endpoint, cluster_name, command_type, command_name, repr(kwargs))

  async def on(self, soft=False):
    if not self._device:
      return
    await super().on()
    LOG.debug('Sending ON command to "%s"', self._name)
    if soft:
      await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'level_control', 'move_to_level_on_off', timeout=5, level=int(self._level*253) + 1, time=TRANSITION_TIME_SOFT)
    else:
      await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'onoff', 'on', timeout=5)
    LOG.debug(' --> done ("%s")', self._name)

  async def off(self, soft=False):
    if not self._device:
      return
    await super().off()
    #await self.configure_reporting()
    LOG.debug('Sending OFF command to "%s"', self._name)
    if soft:
      await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'level_control', 'move_to_level_on_off', timeout=5, level=0, time=TRANSITION_TIME_SOFT)
    else:
      await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'onoff', 'off', timeout=5)
    LOG.debug(' --> done ("%s")', self._name)

  async def toggle(self):
    if not self._device:
      return
    await super().toggle()
    await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'onoff', 'toggle', timeout=5)

  async def level(self, level=None, delta=None, onoff=False, soft=False):
    if not self._device:
      return
    await super().level(level, delta)
    command = 'move_to_level'
    if onoff:
      command += '_on_off'
    time = TRANSITION_TIME_SOFT if soft else TRANSITION_TIME_HARD
    await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'level_control', command, timeout=5, level=int(self._level*253) + 1, time=time)

  async def hue(self, hue):
    if not self._device:
      return
    await super().hue(hue)
    await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'color', 'move_to_hue', timeout=5, hue=int(hue*255), dir=0, time=TRANSITION_TIME_SOFT)

  async def saturation(self, saturation):
    if not self._device:
      return
    await super().saturation(hue)
    await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'color', 'move_to_saturation', timeout=5, saturation=int(saturation*255), dir=0, time=TRANSITION_TIME_SOFT)

  async def temperature(self, temperature):
    if not self._device:
      return
    await super().temperature(temperature)
    mireds = int(1e6 / temperature)
    await self._device.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'color', 'move_to_color_temperature', timeout=5, mireds=mireds, time=TRANSITION_TIME_SOFT)

  async def disable_reporting(self):
    await self._device.zcl_profile(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'level_control', 'configure_reporting', timeout=5, configs=[
      {
        'attribute': 0,
        'datatype': 'uint8',
        'minimum': 0xffff,
        'maximum': 0x0000,
        'delta': 10,
      }
    ])
    await self._device.zcl_profile(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'onoff', 'configure_reporting', timeout=5, configs=[
      {
        'attribute': 0,
        'datatype': 'bool',
        'minimum': 0xffff,
        'maximum': 0x0000,
      }
    ])

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
    await super().reconfigure()
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
class ZigBeeLightGroup(Light):
  def __init__(self, hazard):
    super().__init__(hazard)
    self._group = None
    self._endpoint = None

  async def create_from_group(self, group):
    self._group = group
    self._name = group._name

    # TODO: Query endpoints from group devices.
    self._endpoint = 3

  async def on(self, soft=False):
    if not self._group:
      return
    await super().on()
    LOG.debug('Sending ON command to group "%s"', self._name)
    if soft:
      await self._group.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'level_control', 'move_to_level_on_off', timeout=5, level=int(self._level*253) + 1, time=TRANSITION_TIME_SOFT)
    else:
      await self._group.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'onoff', 'on', timeout=5)
    LOG.debug(' --> done ("%s")', self._name)

  async def off(self, soft=False):
    if not self._group:
      return
    await super().off()
    LOG.debug('Sending OFF command to group "%s"', self._name)
    if soft:
      await self._group.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'level_control', 'move_to_level_on_off', timeout=5, level=0, time=TRANSITION_TIME_SOFT)
    else:
      await self._group.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'onoff', 'off', timeout=5)
    LOG.debug(' --> done ("%s")', self._name)

  async def toggle(self):
    if not self._group:
      return
    await super().toggle()
    await self._group.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'onoff', 'toggle', timeout=5)

  async def level(self, level=None, delta=None, onoff=False, soft=False):
    if not self._group:
      return
    await super().level(level, delta)
    command = 'move_to_level'
    if onoff:
      command += '_on_off'
    time = TRANSITION_TIME_SOFT if soft else TRANSITION_TIME_HARD
    await self._group.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'level_control', command, timeout=5, level=int(self._level*253) + 1, time=time)

  async def hue(self, hue):
    if not self._group:
      return
    await super().hue(hue)
    await self._group.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'color', 'move_to_hue', timeout=5, hue=int(hue*255), dir=0, time=TRANSITION_TIME_SOFT)

  async def temperature(self, temperature):
    if not self._group:
      return
    await super().temperature(temperature)
    mireds = int(1e6 / temperature)
    await self._group.zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, self._endpoint, 'color', 'move_to_color_temperature', timeout=5, mireds=mireds, time=TRANSITION_TIME_SOFT)

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

  def _features(self):
    return super()._features() + ['group'];
