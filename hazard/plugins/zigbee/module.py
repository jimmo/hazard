class ZigBeeModule():
  def __init__(self):
    self._callbacks= {}
    self._unknown = None

  def load_json(self, json):
    pass

  def to_json(self):
    return {
      'type': type(self).__name__
    }

  def set_unknown_device_handler(self, callback):
    self._unknown = callback

  def set_device_handler(self, addr64, callback):
    self._callbacks[addr64] = callback

  def connect(self, port, baudrate):
    pass

  async def get_coordinator_addr64(self):
    pass

  async def get_pan_id(self):
    pass

  async def unicast(self, addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data):
    pass

  async def multicast(self, group_addr, source_endpoint, dest_endpoint, cluster, profile, data):
    pass

  async def broadcast(self, addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data):
    pass

  async def allow_joining(self, allow):
    pass

  def _on_device_frame(self, addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data):
    print('Frame from {}/{} {} {} {} {} -- {}'.format(addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data))
    if addr64 in self._callbacks:
      self._callbacks[addr64](addr16, source_endpoint, dest_endpoint, cluster, profile, data)
    elif self._unknown:
      self._unknown(addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data)
