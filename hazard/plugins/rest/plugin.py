import aiohttp

from hazard.plugin import HazardPlugin, register_plugin
from hazard.thing import get_thing_types


@register_plugin
class RestPlugin(HazardPlugin):
  def __init__(self, hazard):
    super().__init__(hazard)

  def get_routes(self):
    return [
      aiohttp.web.get('/api/rest/thing/list', self.handle_thing_list),
      aiohttp.web.get('/api/rest/thing/types', self.handle_thing_type_list),
      aiohttp.web.post('/api/rest/thing/{id}', self.handle_thing),
      aiohttp.web.post('/api/rest/thing/{id}/action/{action}', self.handle_thing_action),
    ]

  def _get_thing_or_404(self, request):
    thing_id = int(request.match_info['id'])
    if thing_id not in self._hazard._things:
      raise aiohttp.web.HTTPNotFound('Unknown thing')
    return self._hazard._things[thing_id]

  async def handle_thing(self, request):
    thing = self._get_thing_or_404(request)
    data = await request.json()
    thing.load_json(data)
    self._hazard.save()
    return aiohttp.web.json_response(thing.to_json())

  async def handle_thing_list(self, request):
    return aiohttp.web.json_response([t.to_json() for t in self._hazard._things.values()])

  async def handle_thing_type_list(self, request):
    return aiohttp.web.json_response([{
        'type': t,
      } for t in get_thing_types()])

  async def handle_thing_action(self, request):
    thing = self._get_thing_or_404(request)
    data = await request.json()
    await thing.action(request.match_info['action'], data)
    return aiohttp.web.json_response({})
