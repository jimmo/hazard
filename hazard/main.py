import aiohttp.web
import asyncio
import logging
import signal
import sys
import warnings

import zcl.spec

from hazard.hazard import Hazard

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)7s: %(message)s',
    filename='hazard.log',
)
LOG = logging.getLogger('main')


def signal_handler(_signal, _frame):
  loop = asyncio.get_event_loop()
  loop.stop()


def main():
  signal.signal(signal.SIGINT, signal_handler)

  h = Hazard()
  h.load()

  loop = asyncio.get_event_loop()
  warnings.simplefilter('always', ResourceWarning)

  app = aiohttp.web.Application()
  app.add_routes(h.get_routes())
  aiohttp.web.run_app(app)
  LOG.info('Shutting down...')


if __name__ == '__main__':
  main()
