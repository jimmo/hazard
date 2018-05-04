import aiohttp.web

from hazard.plugin import HazardPlugin, register_plugin

from hazard.plugins.zigbee.network import ZigBeeNetwork
from hazard.plugins.zigbee.xbee import XBeeModule


@register_plugin
class ZigBeePlugin(HazardPlugin):
  def __init__(self, hazard):
    super().__init__(hazard)
    self._module = None
    self._network = None

  def load_json(self, json):
    super().load_json(json)
    module = json.get('module', {})
    if module:
      if module['type'] == 'XBeeModule':
        self._module = XBeeModule()
      else:
        raise ValueError('Unknown zigbee module type')
      self._module.load_json(module)
    self._network = ZigBeeNetwork(self._module)
    self._network.load_json(json.get('network', {}))

  def to_json(self):
    json = super().to_json()
    if self._module:
      json['module'] = self._module.to_json(),
    if self._network:
      json['network'] = self._network.to_json(),
    return json

  def get_routes(self):
    return [
      aiohttp.web.get('/zigbee', self.handle_zigbee),
      aiohttp.web.get('/api/zigbee/spec', self.handle_spec),
      aiohttp.web.get('/api/zigbee/status', self.handle_status),
      aiohttp.web.get('/api/zigbee/device/list', self.handle_list_device),
      aiohttp.web.post('/api/zigbee/device/{device}', self.handle_device),
      aiohttp.web.post('/api/zigbee/device/{device}/zdo/{cluster_name}', self.handle_device_zdo),
      aiohttp.web.post('/api/zigbee/device/{device}/zcl/profile/{profile}/{endpoint}/{cluster_name}/{command_name}', self.handle_device_profile_zcl),
      aiohttp.web.post('/api/zigbee/device/{device}/zcl/cluster/{profile}/{endpoint}/{cluster_name}/{command_name}', self.handle_device_cluster_zcl),
      aiohttp.web.post('/api/zigbee/group/{group}/zcl/cluster/{profile}/{endpoint}/{cluster_name}/{command_name}', self.handle_group_cluster_zcl),
    ]

  async def handle_zigbee(self, request):
    return aiohttp.web.FileResponse('hazard/plugins/zigbee/html/zigbee.html')

  async def handle_spec(self, request):
    return aiohttp.web.json_response(zcl.spec.get_json())

  async def handle_status(self, request):
    return aiohttp.web.json_response({
      'coordinator_addr64': '0x{:08x}'.format(await self._module.get_coordinator_addr64()),
      'pan_id': '0x{:08x}'.format(await self._module.get_pan_id()),
    })

  async def handle_list_device(self, request):
    result = [device.to_json() for device in self._network.all_devices()]
    return aiohttp.web.json_response(result)

  async def handle_device(self, request):
    data = await request.json()
    device = self.get_device_from_request(request)
    device.update_from_json(data)
    self._save()
    return aiohttp.web.json_response(device.to_json())

  def get_device_from_request(self, request):
    addr64 = int(request.match_info['device'], 16)
    device = self._network.find_device(addr64)
    if not device:
      raise aiohttp.web.HTTPNotFound('Unknown device')
    return device

  def get_profile_from_request(self, request):
    profile = zcl.spec.get_profile_by_name(request.match_info['profile'])
    if not profile:
      return aiohttp.web.HTTPNotFound('Unknown profile')
    return profile

  async def handle_device_zdo(self, request):
    device = self.get_device_from_request(request)
    cluster_name = request.match_info['cluster_name']
    kwargs = await request.json()
    result = await device.zdo(cluster_name, **kwargs)
    return aiohttp.web.json_response(result)

  async def handle_device_profile_zcl(self, request):
    device = self.get_device_from_request(request)
    profile = self.get_profile_from_request(request)
    kwargs = await request.json()
    result = await device.zcl_profile(profile, int(request.match_info['endpoint'], 10), request.match_info['cluster_name'], request.match_info['command_name'], **kwargs)
    return aiohttp.web.json_response(result)

  async def handle_device_cluster_zcl(self, request):
    device = self.get_device_from_request(request)
    profile = self.get_profile_from_request(request)
    kwargs = await request.json()
    result = await device.zcl_cluster(profile, int(request.match_info['endpoint'], 10), request.match_info['cluster_name'], request.match_info['command_name'], **kwargs)
    return aiohttp.web.json_response(result)

  async def handle_group_cluster_zcl(self, request):
    group_addr16 = int(request.match_info['group'], 10)
    profile = self.get_profile_from_request(request)
    kwargs = await request.json()
    result = await self._network.zcl_cluster_group(group_addr16, profile, int(request.match_info['endpoint'], 10), request.match_info['cluster_name'], request.match_info['command_name'], **kwargs)
    return aiohttp.web.json_response(result)
