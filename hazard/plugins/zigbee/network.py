import zcl.spec

from hazard.plugins.zigbee.common import ZigBeeDeliveryFailure
from hazard.plugins.zigbee.device import ZigBeeDevice


class ZigBeeNetwork():
  def __init__(self, module):
    self._module = module
    if self._module:
      self._module.set_unknown_device_handler(self._on_unknown_device_frame)
    self._devices = {}

  def to_json(self):
    return {
      'devices': [d.to_json() for d in self._devices.values()]
    }

  def load_json(self, json):
    for device_config in json.get('devices', []):
      device = ZigBeeDevice.from_json(self, device_config)
      self._devices[device._addr64] = device

  def _save(self):
    pass

  def _on_unknown_device_frame(self, addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data):
    if addr64 not in self._devices:
      self._devices[addr64] = ZigBeeDevice(self, addr64, addr16)
    self._devices[addr64]._on_frame(source_endpoint, dest_endpoint, cluster, profile, data)
    self._save()

  def all_devices(self):
    return self._devices.values()

  async def _send_group(self, group_addr16, seq, source_endpoint, dest_endpoint, cluster, profile, data, timeout):
    if profile == zcl.spec.Profile.ZIGBEE_LIGHT_LINK:
      profile = zcl.spec.Profile.HOME_AUTOMATION

    result = await self._module.multicast(group_addr16, source_endpoint, dest_endpoint, cluster, profile, data)
    if not result:
      raise ZigBeeDeliveryFailure()

  async def zdo_group(self, group_addr16, cluster_name, timeout=10, **kwargs):
    seq = 127
    cluster, data = zcl.spec.encode_zdo(cluster_name, seq, **kwargs)
    return await self._send_group(group_addr16, seq, 0, 0, cluster, zcl.spec.Profile.ZIGBEE, data, timeout)

  async def zcl_cluster_group(self, group_addr16, profile, dest_endpoint, cluster_name, command_name, timeout=5, **kwargs):
    seq = 127
    cluster, data = zcl.spec.encode_cluster_command(cluster_name, command_name, seq, 0, **kwargs)
    return await self._send_group(group_addr16, seq, 1, dest_endpoint, cluster, profile, data, timeout)

  async def zcl_profile_group(self, group_addr16, profile, dest_endpoint, cluster_name, command_name, timeout=5, **kwargs):
    seq = 127
    cluster, data = zcl.spec.encode_profile_command(cluster_name, command_name, seq, 0, **kwargs)
    return await self._send_group(group_addr16, seq, 1, dest_endpoint, cluster, profile, data, timeout)
