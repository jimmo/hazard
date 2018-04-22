import asyncio
import signal
import sys

from .zigbee import zigbee
from .zigbee import xbee


def signal_handler(_signal, _frame):
  loop = asyncio.get_event_loop()
  loop.stop()


def main():
  signal.signal(signal.SIGINT, signal_handler)
  x = xbee.XBeeModule()
  x.connect(sys.argv[1], 115200)

  z = zigbee.ZigBeeNetwork(x)

  loop = asyncio.get_event_loop()
  loop.create_task(z.ping())
  loop.run_forever()
  loop.close()


if __name__ == '__main__':
  main()
