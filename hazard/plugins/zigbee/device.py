import asyncio
import async_timeout

import zcl.spec


class ZigBeeDevice():
  def __init__(self, network, addr64=0, addr16=0, name=''):
    self._network = network
    self._addr64 = addr64
    self._addr16 = addr16
    self._name = name or 'Unknown {}'.format(self.addr64hex())
    if self._addr64:
      self._network._module.set_device_handler(self._addr64, self._on_frame)
    self._seq = 1
    self._inflight = {}
    self._on_zcl_callback = None

  def register_zcl(self, callback):
    self._on_zcl_callback = callback

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
      print('  delivering future')
      self._inflight[seq].set_result(kwargs)

  def _on_zcl(self, source_endpoint, dest_endpoint, cluster, profile, data):
    print('zcl', source_endpoint, dest_endpoint, cluster, profile, data)
    cluster_name, seq, command_type, command_name, kwargs = zcl.spec.decode_zcl(cluster, data)
    if seq in self._inflight:
      self._inflight[seq].set_result((command_name, kwargs,))
    elif self._on_zcl:
      asyncio.get_event_loop().create_task(self._on_zcl_callback(source_endpoint, dest_endpoint, cluster_name, command_type, command_name, **kwargs))

  def _next_seq(self):
    seq = self._seq
    self._seq = (self._seq + 1) % 256 or 1
    return seq

  async def _send(self, seq, source_endpoint, dest_endpoint, cluster, profile, data, timeout):
    if profile == zcl.spec.Profile.ZIGBEE_LIGHT_LINK:
      profile = zcl.spec.Profile.HOME_AUTOMATION

    f = asyncio.Future()
    self._inflight[seq] = f
    #print(hex(seq))
    result = await self._network._module.unicast(self._addr64, self._addr16, source_endpoint, dest_endpoint, cluster, profile, data)
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

  async def zdo(self, cluster_name, timeout=10, **kwargs):
    seq = self._next_seq()
    cluster, data = zcl.spec.encode_zdo(cluster_name, seq, **kwargs)
    return await self._send(seq, 0, 0, cluster, zcl.spec.Profile.ZIGBEE, data, timeout)

  async def zcl_cluster(self, profile, dest_endpoint, cluster_name, command_name, timeout=5, **kwargs):
    seq = self._next_seq()
    cluster, data = zcl.spec.encode_cluster_command(cluster_name, command_name, seq, 0, **kwargs)
    return await self._send(seq, 1, dest_endpoint, cluster, profile, data, timeout)

  async def zcl_profile(self, profile, dest_endpoint, cluster_name, command_name, timeout=5, **kwargs):
    seq = self._next_seq()
    cluster, data = zcl.spec.encode_profile_command(cluster_name, command_name, seq, 0, **kwargs)
    return await self._send(seq, 1, dest_endpoint, cluster, profile, data, timeout)

  # async def _on_endpoint(self, status, addr16, simple_descriptors):
  #   print('endpoint info', status, addr16, simple_descriptors)

  # async def _on_endpoints(self, status, addr16, active_eps):
  #   print('endpoint', status, addr16, active_eps)
  #   for endpoint in active_eps:
  #     descriptors = await self.zdo('simple_desc', addr16=self._addr16, endpoint=endpoint)
  #     await self._on_endpoint(**descriptors)

  def addr64hex(self):
    return '0x{:08x}'.format(self._addr64)

  def to_json(self):
    return {
      'addr64': self.addr64hex(),
      'addr16': self._addr16,
      'name': self._name,
    }

  def load_json(self, device_config):
    self._addr64 = int(device_config['addr64'], 16)
    self._addr16 = device_config['addr16']
    self._name = device_config.get('name', '')
    self._network._module.set_device_handler(self._addr64, self._on_frame)

  def update_from_json(self, device_config):
    if self._addr64 != int(device_config['addr64'], 16):
      raise ValueError('Updating from incorrect device')
    self._name = device_config.get('name', '')
