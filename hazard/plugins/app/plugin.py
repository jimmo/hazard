import aiohttp

from hazard.plugin import HazardPlugin, register_plugin


@register_plugin
class AppPlugin(HazardPlugin):
    def __init__(self, hazard):
        super().__init__(hazard)

    def get_routes(self):
        return [
            aiohttp.web.get("/", self.handle_app),
            aiohttp.web.get("/app.js", self.handle_app_js),
            aiohttp.web.get("/app.js.map", self.handle_app_js_map),
            aiohttp.web.get("/ionicons.woff2", self.handle_app_icons),
        ]

    async def start(self):
        pass

    async def handle_app(self, request):
        return aiohttp.web.FileResponse("hazard/plugins/app/app.html")

    async def handle_app_js(self, request):
        return aiohttp.web.FileResponse("hazard/plugins/app/dist/app.js")

    async def handle_app_js_map(self, request):
        return aiohttp.web.FileResponse("hazard/plugins/app/dist/app.js.map")

    async def handle_app_icons(self, request):
        return aiohttp.web.FileResponse("hazard/plugins/app/ionicons.woff2")
