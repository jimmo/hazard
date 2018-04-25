import aiohttp.web
import asyncio
import signal
import sys

import zcl.spec

from .zigbee import zigbee
from .zigbee import xbee


z = None


def signal_handler(_signal, _frame):
  loop = asyncio.get_event_loop()
  loop.stop()


async def handle_main(request):
  return aiohttp.web.FileResponse('hazard/html/zigbee.html')


async def handle_js(request):
  return aiohttp.web.FileResponse('hazard/js/{}'.format(request.match_info['file']))


async def handle_css(request):
  return aiohttp.web.FileResponse('hazard/css/{}'.format(request.match_info['file']))


def main():
  global z
  signal.signal(signal.SIGINT, signal_handler)
  x = xbee.XBeeModule()
  x.connect(sys.argv[1], 115200)

  z = zigbee.ZigBeeNetwork(x)
  loop = asyncio.get_event_loop()
  loop.create_task(z.ping())

  app = aiohttp.web.Application()
  app.add_routes([
    aiohttp.web.get('/', handle_main),
    aiohttp.web.get('/js/{file}', handle_js),
    aiohttp.web.get('/css/{file}', handle_css),
  ] + z.get_rest_routes())
  aiohttp.web.run_app(app)


if __name__ == '__main__':
  main()
