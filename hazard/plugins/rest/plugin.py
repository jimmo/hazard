import aiohttp

from hazard.plugin import HazardPlugin, register_plugin
from hazard.thing import get_thing_types


@register_plugin
class RestPlugin(HazardPlugin):
  def __init__(self, hazard):
    super().__init__(hazard)

  def get_routes(self):
    return [
      aiohttp.web.get('/api/rest/reconfigure', self.handle_reconfigure),
      aiohttp.web.get('/api/rest/action/list', self.handle_action_list),
      aiohttp.web.post('/api/rest/action/create', self.handle_action_create),
      aiohttp.web.post('/api/rest/action/{id}', self.handle_action),
      aiohttp.web.post('/api/rest/action/{id}/remove', self.handle_action_remove),
      aiohttp.web.post('/api/rest/action/{id}/invoke', self.handle_action_invoke),
      aiohttp.web.get('/api/rest/thing/list', self.handle_thing_list),
      aiohttp.web.get('/api/rest/thing/types', self.handle_thing_type_list),
      aiohttp.web.post('/api/rest/thing/{id}', self.handle_thing),
      aiohttp.web.post('/api/rest/thing/{id}/remove', self.handle_thing_remove),
      aiohttp.web.post('/api/rest/thing/{id}/action/{action}', self.handle_thing_action),
    ]

  def _get_action_or_404(self, request):
    action_id = int(request.match_info['id'])
    if action_id not in self._hazard._actions:
      raise aiohttp.web.HTTPNotFound('Unknown action')
    return self._hazard._actions[action_id]

  def _get_thing_or_404(self, request):
    thing_id = int(request.match_info['id'])
    if thing_id not in self._hazard._things:
      raise aiohttp.web.HTTPNotFound('Unknown thing')
    return self._hazard._things[thing_id]

  async def handle_reconfigure(self, request):
    await self._hazard.reconfigure()
    return aiohttp.web.json_response({})

  async def handle_action(self, request):
    action = self._get_action_or_404(request)
    data = await request.json()
    action.load_json(data)
    self._hazard.save()
    return aiohttp.web.json_response(action.to_json())

  async def handle_action_list(self, request):
    return aiohttp.web.json_response([a.to_json() for a in self._hazard._actions.values()])

  async def handle_action_create(self, request):
    data = await request.json()
    action = self._hazard.create_action()
    action.load_json(data)
    self._hazard.save()
    return aiohttp.web.json_response(action.to_json())

  async def handle_action_remove(self, request):
    action = self._get_action_or_404(request)
    action.remove()
    self._hazard.save()
    return aiohttp.web.json_response(action.to_json())

  async def handle_action_invoke(self, request):
    action = self._get_action_or_404(request)
    data = await request.json()
    action.invoke(data)
    return aiohttp.web.json_response({})

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

  async def handle_thing_remove(self, request):
    thing = self._get_thing_or_404(request)
    thing.remove()
    return aiohttp.web.json_response({})
