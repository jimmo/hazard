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
  text = "Hazard"
  return aiohttp.web.Response(text=text)


async def handle_zigbee_zdo(request):
  return aiohttp.web.Response()


async def handle_zigbee_profile_zcl(request):
  return aiohttp.web.Response()


async def handle_zigbee_cluster_zcl(request):
  profile_name = request.match_info['profile']
  endpoint = int(request.match_info['endpoint'])
  cluster_name = request.match_info['cluster_name']
  command_name = request.match_info['command_name']
  kwargs = {}
  await z._devices[9518399593889494811].zcl(zcl.spec.Profile.HOME_AUTOMATION, endpoint, cluster_name, command_name, **kwargs)
  return aiohttp.web.Response()


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
                  aiohttp.web.post('/api/zigbee/{device}/zdo/{cluster_name}', handle_zigbee_zdo),
                  aiohttp.web.post('/api/zigbee/{device}/{profile}/{endpoint}/zcl/{cluster_name}/profile/{command_name}', handle_zigbee_profile_zcl),
                  aiohttp.web.get('/api/zigbee/{device}/{profile}/{endpoint}/zcl/{cluster_name}/cluster/{command_name}', handle_zigbee_cluster_zcl),
  ])
  aiohttp.web.run_app(app)


if __name__ == '__main__':
  main()
