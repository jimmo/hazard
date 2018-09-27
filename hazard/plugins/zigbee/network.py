import zcl.spec

from hazard.plugins.zigbee.common import ZigBeeDeliveryFailure
from hazard.plugins.zigbee.device import ZigBeeDevice
from hazard.plugins.zigbee.group import ZigBeeGroup


class ZigBeeNetwork():
  def __init__(self, hazard, module):
    self._hazard = hazard
    self._module = module
    self._module.set_unknown_device_handler(self._on_unknown_device_frame)
    self._devices = {}
    self._groups = {}

  def to_json(self):
    return {
      'devices': [d.to_json() for d in self._devices.values()],
      'groups': [g.to_json() for g in self._groups.values()],
    }

  def load_json(self, json):
    for device_config in json.get('devices', []):
      device = ZigBeeDevice(self)
      device.load_json(device_config)
      self._devices[device._addr64] = device
    for group_config in json.get('groups', []):
      group = ZigBeeGroup(self)
      group.load_json(group_config)
      self._groups[group._addr16] = group

  def _on_unknown_device_frame(self, addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data):
    if addr64 not in self._devices:
      self._devices[addr64] = ZigBeeDevice(self, addr64, addr16)
    self._devices[addr64]._on_frame(addr16, source_endpoint, dest_endpoint, cluster, profile, data)
    self._hazard.save()

  def all_devices(self):
    return self._devices.values()

  def all_groups(self):
    return self._groups.values()

  def find_device(self, addr64):
    if isinstance(addr64, str):
      addr64 = int(addr64, 16)
    return self._devices.get(addr64, None)

  def find_group(self, addr16):
    return self._groups.get(addr16, None)
  
  def remove_group(self, addr16):
    del self._groups[addr16]

  def create_group(self):
    for i in range(1, 65535):
      if i in self._groups:
        continue
      group = ZigBeeGroup(self, i, 'New Group')
      self._groups[i] = group
      self._hazard.save()
      return group
