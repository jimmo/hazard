import aiohttp.web
import asyncio
import signal
import sys

import zcl.spec

from hazard.plugins.zigbee import zigbee
from hazard.plugins.zigbee import xbee

from hazard.hazard import Hazard


def signal_handler(_signal, _frame):
  loop = asyncio.get_event_loop()
  loop.stop()


def main():
  signal.signal(signal.SIGINT, signal_handler)

  h = Hazard()
  h.load()

  #x = xbee.XBeeModule()
  #x.connect(sys.argv[1], 115200)

  #z = zigbee.ZigBeeNetwork(x)
  #loop = asyncio.get_event_loop()
  #loop.create_task(z.ping())

  #h = home.Home()

  app = aiohttp.web.Application()
  app.add_routes(h.get_routes())
  aiohttp.web.run_app(app)


if __name__ == '__main__':
  main()
