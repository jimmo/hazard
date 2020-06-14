from hazard.plugin import HazardPlugin, register_plugin

import hazard.plugins.ble.things

import asyncio
import bleak
import logging
import os

LOG = logging.getLogger('hazard')

@register_plugin
class BlePlugin(HazardPlugin):
  def __init__(self, hazard):
    super().__init__(hazard)
    self._registered_ble_names = {}

  def load_json(self, json):
    super().load_json(json)

  def register_advertisement(self, name, callback):
    self._registered_ble_names[name] = callback

  async def _scan(self):
    while True:
      devices = await bleak.discover()
      LOG.debug('BLE scan found %d devices', len(devices))
      for d in devices:
        manuf = d.metadata.get('manufacturer_data', {}).get(65535, [])
        if d.name.startswith('th') and len(d.name) == 10:
          if d.name in self._registered_ble_names:
            self._registered_ble_names[d.name](d, manuf)
          else:
            LOG.info('Unknown temperature sensor %s', d.name)
      os.system('echo remove \'*-*\' | bluetoothctl > /dev/null 2>&1')

  def start(self):
    loop = asyncio.get_event_loop()
    loop.create_task(self._scan())

  def to_json(self):
    json = super().to_json()
    return json
