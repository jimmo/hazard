import aiohttp.web
import asyncio
import async_timeout
import json

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
      print('  delivering future')
      self._inflight[seq].set_result(kwargs)

  def _on_zcl(self, source_endpoint, dest_endpoint, cluster, profile, data):
    print('zcl', source_endpoint, dest_endpoint, cluster, profile, data)
    cluster_name, seq, command_type, command_name, kwargs = zcl.spec.decode_zcl(cluster, data)
    if seq in self._inflight:
      self._inflight[seq].set_result((command_name, kwargs,))
    if self._addr64 == 0x137a000001385b:
      asyncio.get_event_loop().create_task(self._network._devices[0x84182600000186f8].zcl_cluster(zcl.spec.Profile.HOME_AUTOMATION, 3, 'onoff', 'toggle'))

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

  async def ping(self):
    print('ping device ', hex(self._addr64))

  def config(self):
    return {
      'addr64': '0x{:08x}'.format(self._addr64),
      'addr16': self._addr16,
    }


class ZigBeeNetwork():
  def __init__(self, zigbee_module):
    self._zigbee_module = zigbee_module
    self._zigbee_module.set_unknown_device_handler(self._on_unknown_device_frame)
    self._devices = {}
    try:
      with open('/home/jimmo/.hazard', 'r') as f:
        config = json.load(f)
        for device in config.get('devices', []):
          addr64 = int(device['addr64'], 16)
          self._devices[addr64] = ZigBeeDevice(self, addr64, device['addr16'])
    except FileNotFoundError:
      pass
    except json.decoder.JSONDecodeError:
      pass

  def _save(self):
    with open('/home/jimmo/.hazard', 'w') as f:
      json.dump({'devices': [d.config() for d in self._devices.values()]}, f)

  def _on_unknown_device_frame(self, addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data):
    if addr64 not in self._devices:
      self._devices[addr64] = ZigBeeDevice(self, addr64, addr16)
    self._devices[addr64]._on_frame(source_endpoint, dest_endpoint, cluster, profile, data)
    self._save()

  async def ping(self):
    pass
    # while True:
    #   await asyncio.sleep(2)
    #   for d in self._devices.values():
    #     await d.ping()
    #     await asyncio.sleep(0.1)
      # for d in self._devices.values():
      #   try:
      #     await d.zcl(zcl.spec.Profile.HOME_AUTOMATION, 3, 'level_control', 'move_to_level', level=180, time=5)
      #   except:
      #     pass
      # await asyncio.sleep(2)
      # for d in self._devices.values():
      #   try:
      #     await d.zcl(zcl.spec.Profile.HOME_AUTOMATION, 3, 'level_control', 'move_to_level', level=20, time=5)
      #   except:
      #     pass

  def get_rest_routes(self):
    return [
      aiohttp.web.get('/api/zigbee/spec', self.handle_rest_spec),
      aiohttp.web.get('/api/zigbee/status', self.handle_rest_status),
      aiohttp.web.get('/api/zigbee/devices', self.handle_rest_devices),
      aiohttp.web.post('/api/zigbee/zdo/{device}/{cluster_name}', self.handle_rest_zdo),
      aiohttp.web.post('/api/zigbee/zcl/profile/{device}/{profile}/{endpoint}/{cluster_name}/{command_name}', self.handle_rest_profile_zcl),
      aiohttp.web.post('/api/zigbee/zcl/cluster/{device}/{profile}/{endpoint}/{cluster_name}/{command_name}', self.handle_rest_cluster_zcl),
    ]

  async def handle_rest_spec(self, request):
    return aiohttp.web.json_response(zcl.spec.get_json())

  async def handle_rest_status(self, request):
    return aiohttp.web.json_response({
      'coordinator_addr64': '0x{:08x}'.format(await self._zigbee_module.get_coordinator_addr64()),
      'pan_id': '0x{:08x}'.format(await self._zigbee_module.get_pan_id()),
    })

  async def handle_rest_devices(self, request):
    result = [{ 'addr64': '0x{:08x}'.format(device._addr64), 'addr16': device._addr16 } for device in self._devices.values()]
    return aiohttp.web.json_response(result)

  def get_device_from_request(self, request):
    addr64 = int(request.match_info['device'], 16)
    if addr64 not in self._devices:
      raise aiohttp.web.HTTPNotFound('Unknown device')
    return self._devices[addr64]

  def get_profile_from_request(self, request):
    profile = zcl.spec.get_profile_by_name(request.match_info['profile'])
    if not profile:
      return aiohttp.web.HTTPNotFound('Unknown profile')
    return profile

  async def handle_rest_zdo(self, request):
    device = self.get_device_from_request(request)
    cluster_name = request.match_info['cluster_name']
    kwargs = await request.json()
    result = await device.zdo(cluster_name, **kwargs)
    return aiohttp.web.json_response(result)

  async def handle_rest_profile_zcl(self, request):
    device = self.get_device_from_request(request)
    profile = self.get_profile_from_request(request)
    kwargs = await request.json()
    result = await device.zcl_profile(profile, int(request.match_info['endpoint'], 10), request.match_info['cluster_name'], request.match_info['command_name'], **kwargs)
    return aiohttp.web.json_response(result)

  async def handle_rest_cluster_zcl(self, request):
    device = self.get_device_from_request(request)
    profile = self.get_profile_from_request(request)
    kwargs = await request.json()
    result = await device.zcl_cluster(profile, int(request.match_info['endpoint'], 10), request.match_info['cluster_name'], request.match_info['command_name'], **kwargs)
    return aiohttp.web.json_response(result)
