from hazard.plugin import HazardPlugin, register_plugin


@register_plugin
class ZigBeePlugin(HazardPlugin):
  def __init__(self, hazard):
    super().__init__(hazard)

  def load_json(self, json):
    pass
            #for device_config in config.get('devices', []):
        #  device = ZigBeeDevice.from_json(self, device_config)
        #  self._devices[device._addr64] = device
