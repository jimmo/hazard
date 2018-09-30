import aiohttp.web
import asyncio
import logging
import signal
import sys
import warnings

import zcl.spec

from hazard.hazard import Hazard

# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(levelname)7s: %(message)s',
#     stream=sys.stderr,
# )
# LOG = logging.getLogger('')

def signal_handler(_signal, _frame):
  loop = asyncio.get_event_loop()
  loop.stop()


def main():
  signal.signal(signal.SIGINT, signal_handler)

  h = Hazard()
  h.load()

  loop = asyncio.get_event_loop()
  #loop.set_debug(True)
  warnings.simplefilter('always', ResourceWarning)


  app = aiohttp.web.Application()
  app.add_routes(h.get_routes())
  aiohttp.web.run_app(app)


if __name__ == '__main__':
  main()
