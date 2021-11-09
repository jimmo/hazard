import json
import logging

from hazard.thing import register_thing
from hazard.things import MultiSensor

import zcl.spec

LOG = logging.getLogger('hazard')


@register_thing
class ZigBeeMultiSensor(MultiSensor):
  def __init__(self, hazard):
    super().__init__(hazard)
    self._device = None

  async def _on_zcl(self, source_endpoint, dest_endpoint, cluster_name, command_type, command_name, **kwargs):
    # print('multi sensor', source_endpoint, dest_endpoint, cluster_name, command_type, command_name, repr(kwargs))

    if cluster_name == 'ias_zone' and command_name == 'zone_enrol_request':
        LOG.info('Enrolling multi sensor')
        await self._device.zcl_cluster(0x0104, 1, 'ias_zone', 'zone_enrol', enroll_response_code=0, zone_id=0xff)
    elif cluster_name == 'ias_zone' and command_name == 'zone_status_change':
        zone_status = kwargs.get('zone_status', 0)
        await self.invoke_openclose(zone_status & 1)

  async def _on_announce(self):
    LOG.info('Auto-binding multi sensor')
    coordinator_addr64 = await self._device._network._module.get_coordinator_addr64()
    await self._device.zcl_profile(zcl.spec.Profile.HOME_AUTOMATION, 1, 'ias_zone', 'write_attributes', attributes=[{'attribute': 0x0010, 'datatype': 'EUI64', 'value': coordinator_addr64}])

  async def create_from_device(self, device):
    self._device = device
    self._device.register_zcl(self._on_zcl)
    self._device.register_announce(self._on_announce)
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
    self._device.register_announce(self._on_announce)

