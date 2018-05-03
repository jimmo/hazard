import aiohttp

from hazard.plugin import HazardPlugin, register_plugin


@register_plugin
class WebPlugin(HazardPlugin):
  def __init__(self, hazard):
    super().__init__(hazard)

  def get_routes(self):
    return [
      aiohttp.web.get('/', self.handle_home),
    ]

  async def handle_home(self, request):
    return aiohttp.web.FileResponse('hazard/plugins/web/html/home.html')
