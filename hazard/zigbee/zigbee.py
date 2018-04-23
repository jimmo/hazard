import asyncio
import async_timeout

import zcl.spec

class ZigBeeModule():
  def __init__(self):
    self._callbacks= {}
    self._unknown = None

  def set_unknown_device_handler(self, callback):
    self._unknown = callback

  def set_device_handler(self, addr64, callback):
    self._callbacks[addr64] = callback

  def connect(self, port, baudrate):
    pass

  async def unicast(self, addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data):
    pass

  async def multicast(self, group_addr, source_endpoint, dest_endpoint, cluster, profile, data):
    pass

  async def broadcast(self, addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data):
    pass

  def _on_device_frame(self, addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data):
    print('Frame from {}/{} {} {} {} {} -- {}'.format(addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data))
    if addr64 in self._callbacks:
      self._callbacks[addr64](source_endpoint, dest_endpoint, cluster, profile, data)
    elif self._unknown:
      self._unknown(addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data)


class ZigBeeTimeout(RuntimeError):
  pass


class ZigBeeDeliveryFailure(RuntimeError):
  pass


class ZigBeeDevice():
  def __init__(self, network, addr64, addr16):
    self._network = network
    self._addr64 = addr64
    self._addr16 = addr16
    self._network._zigbee_module.set_device_handler(self._addr64, self._on_frame)
    self._seq = 1
    self._inflight = {}

  def _on_frame(self, source_endpoint, dest_endpoint, cluster, profile, data):
    #print('Received frame from device', source_endpoint, dest_endpoint, cluster, profile, data)
    if profile == zcl.spec.Profile.ZIGBEE and dest_endpoint == zcl.spec.Endpoint.ZDO:
      self._on_zdo(cluster, data)
    else:
      self._on_zcl(source_endpoint, dest_endpoint, cluster, profile, data)

  def _on_zdo(self, cluster, data):
    #print('zdo', self._addr64, self._addr16, cluster, data)
    cluster_name, seq, kwargs = zcl.spec.decode_zdo(cluster, data)
    print('zdo', cluster_name, seq, kwargs)

    if seq in self._inflight:
      self._inflight[seq].set_result(kwargs)

  def _on_zcl(self, source_endpoint, dest_endpoint, cluster, profile, data):
    print('zcl', source_endpoint, dest_endpoint, cluster, profile, data)
    cluster_name, seq, command_type, command_name, kwargs = zcl.spec.decode_zcl(cluster, data)
    if seq in self._inflight:
      self._inflight[seq].set_result((command_name, kwargs,))

  def _next_seq(self):
    seq = self._seq
    self._seq = (self._seq + 1) % 256 or 1
    return seq

  async def _send(self, seq, source_endpoint, dest_endpoint, cluster, profile, data, timeout):
    f = asyncio.Future()
    self._inflight[seq] = f
    print(hex(seq))
    result = await self._network._zigbee_module.unicast(self._addr64, self._addr16, source_endpoint, dest_endpoint, cluster, profile, data)
    if not result:
      f.cancel()
      raise ZigBeeDeliveryFailure()

    try:
      async with async_timeout.timeout(timeout):
        return await f
    except asyncio.TimeoutError:
      raise ZigBeeTimeout()
    finally:
      del self._inflight[seq]

  async def zdo(self, cluster_name, timeout=2, **kwargs):
    seq = self._next_seq()
    cluster, data = zcl.spec.encode_zdo(cluster_name, seq, **kwargs)
    return await self._send(seq, 0, 0, cluster, zcl.spec.Profile.ZIGBEE, data, timeout)

  async def zcl(self, profile, dest_endpoint, cluster_name, command_name, timeout=2, **kwargs):
    seq = self._next_seq()
    cluster, data = zcl.spec.encode_cluster_command(cluster_name, command_name, seq, 0, **kwargs)
    return await self._send(seq, 1, dest_endpoint, cluster, profile, data, timeout)

  async def _on_endpoint(self, status, addr16, simple_descriptors):
    print('endpoint info', status, addr16, simple_descriptors)

  async def _on_endpoints(self, status, addr16, active_eps):
    print('endpoint', status, addr16, active_eps)
    for endpoint in active_eps:
      descriptors = await self.zdo('simple_desc', addr16=self._addr16, endpoint=endpoint)
      await self._on_endpoint(**descriptors)

  async def ping(self):
    print('ping device ', hex(self._addr64))


class ZigBeeNetwork():
  def __init__(self, zigbee_module):
    self._zigbee_module = zigbee_module
    self._zigbee_module.set_unknown_device_handler(self._on_unknown_device_frame)
    self._devices = {}
    #self._devices[0x137a000001385b] = ZigBeeDevice(self, 0x137a000001385b, 18936)  # switch
    self._devices[9518399593889494811] = ZigBeeDevice(self, 9518399593889494811, 13671)
    self._devices[9518399593889425560] = ZigBeeDevice(self, 9518399593889425560, 31399)
    self._devices[9518399593889498872] = ZigBeeDevice(self, 9518399593889498872, 65295)
    self._devices[9518399593889498117] = ZigBeeDevice(self, 9518399593889498117, 57365)


  def _on_unknown_device_frame(self, addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data):
    if addr64 not in self._devices:
      self._devices[addr64] = ZigBeeDevice(self, addr64, addr16)
    self._devices[addr64]._on_frame(source_endpoint, dest_endpoint, cluster, profile, data)

  async def ping(self):
    while True:
      await asyncio.sleep(2)
      for d in self._devices.values():
        try:
          await d.zcl(zcl.spec.Profile.HOME_AUTOMATION, 3, 'level_control', 'move_to_level', level=180, time=5)
        except:
          pass
      await asyncio.sleep(2)
      for d in self._devices.values():
        try:
          await d.zcl(zcl.spec.Profile.HOME_AUTOMATION, 3, 'level_control', 'move_to_level', level=20, time=5)
        except:
          pass
