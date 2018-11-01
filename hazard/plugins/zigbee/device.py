import asyncio
import async_timeout
import logging

from hazard.plugins.zigbee.common import ZigBeeDeliveryFailure, ZigBeeTimeout

import zcl.spec

LOG = logging.getLogger('zigbee')

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
    self._recent_seq = []

  def register_zcl(self, callback):
    self._on_zcl_callback = callback

  def _on_frame(self, addr16, source_endpoint, dest_endpoint, cluster, profile, data):
    if addr16 != self._addr16:
      LOG.info('Updating addr16 on {} (rx: 0x{:04x}, config: 0x{:04x})'.format(self.addr64hex(), addr16, self._addr16))
      self._addr16 = addr16
      self._network._hazard.save()
    if profile == zcl.spec.Profile.ZIGBEE and dest_endpoint == zcl.spec.Endpoint.ZDO:
      self._on_zdo(cluster, data)
    else:
      self._on_zcl(source_endpoint, dest_endpoint, cluster, profile, data)

  def _on_zdo(self, cluster, data):
    cluster_name, seq, kwargs = zcl.spec.decode_zdo(cluster, data)
    LOG.info('ZDO from "{}": {} {}\n   {}'.format(self._name, seq, cluster_name, kwargs))

    if seq in self._inflight:
      #print('  delivering future')
      self._inflight[seq].set_result(kwargs)
      return

    if cluster_name == 'match_desc':
      self._on_match_descriptors(**kwargs)

  def _on_zcl(self, source_endpoint, dest_endpoint, cluster, profile, data):
    cluster_name, seq, command_type, command_name, default_response, kwargs = zcl.spec.decode_zcl(cluster, data)
    LOG.info('ZCL from "{}": {} {} {} {} {} {} {} {} {}'.format(self._name, source_endpoint, dest_endpoint, seq, profile, cluster_name, command_type, command_name, default_response, kwargs))
    if seq in self._inflight:
      self._inflight[seq].set_result((command_name, kwargs,))
      return
    if seq in self._recent_seq:
      LOG.info('Ignoring duplicate ZCL')
      return
    self._recent_seq = self._recent_seq[-50:] + [seq]
    if self._on_zcl_callback:
      asyncio.get_event_loop().create_task(self._on_zcl_callback(source_endpoint, dest_endpoint, cluster_name, command_type, command_name, **kwargs))

  def _on_match_descriptors(profile, in_clusters, addr16, out_clusters):
    if profile == zcl.spec.Profile.HOME_AUTOMATION and in_clusters == [0x0019]:
      # Ignore queries for the ugrade cluster.
      return
    LOG.warning('Attempted to match descriptors: profile {} / in {} / out {}'.format(profile, in_clusters, out_clusters))

  def _next_seq(self):
    seq = self._seq
    self._seq = (self._seq + 1) % 256 or 1
    return seq

  async def _send(self, seq, source_endpoint, dest_endpoint, cluster, profile, data, timeout):
    if profile == zcl.spec.Profile.ZIGBEE_LIGHT_LINK:
      profile = zcl.spec.Profile.HOME_AUTOMATION

    f = asyncio.Future()
    self._inflight[seq] = f
    try:
      #print(hex(seq))
      result = await self._network._module.unicast(self._addr64, self._addr16, source_endpoint, dest_endpoint, cluster, profile, data)
      if not result:
        f.cancel()
        raise ZigBeeDeliveryFailure()

      try:
        async with async_timeout.timeout(timeout):
          return await f
      except asyncio.TimeoutError:
        raise ZigBeeTimeout() from None
    finally:
      del self._inflight[seq]

  async def zdo(self, cluster_name, timeout=10, **kwargs):
    seq = self._next_seq()
    cluster, data = zcl.spec.encode_zdo(cluster_name, seq, **kwargs)
    return await self._send(seq, 0, 0, cluster, zcl.spec.Profile.ZIGBEE, data, timeout)

  async def zcl_cluster(self, profile, dest_endpoint, cluster_name, command_name, timeout=5, **kwargs):
    seq = self._next_seq()
    cluster, data = zcl.spec.encode_cluster_command(cluster_name, command_name, seq, direction=0, default_response=True, **kwargs)
    return await self._send(seq, 1, dest_endpoint, cluster, profile, data, timeout)

  async def zcl_profile(self, profile, dest_endpoint, cluster_name, command_name, timeout=5, **kwargs):
    seq = self._next_seq()
    cluster, data = zcl.spec.encode_profile_command(cluster_name, command_name, seq, direction=0, default_response=True, **kwargs)
    return await self._send(seq, 1, dest_endpoint, cluster, profile, data, timeout)

  def addr64hex(self):
    return '0x{:08x}'.format(self._addr64)

  def addr16(self):
    return self._addr16

  def addr64(self):
    return self._addr64

  def to_json(self):
    return {
      'type': type(self).__name__,
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
