import aiohttp.web
import asyncio
import logging
import logging.handlers
import signal
import sys
import warnings

from hazard.hazard import Hazard

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)7s: %(message)s", handlers=[]
)
LOG = logging.getLogger("hazard")
LOG.addHandler(
    logging.handlers.RotatingFileHandler(
        "hazard.log", maxBytes=4 * 1024**2, backupCount=100000
    )
)


def signal_handler(_signal, _frame):
    loop = asyncio.get_event_loop()
    loop.stop()


def main():
    signal.signal(signal.SIGINT, signal_handler)

    h = Hazard()
    h.load()

    async def background_tasks(app):
        await h.start()
        yield
        await h.stop()

    loop = asyncio.get_event_loop()
    warnings.simplefilter("always", ResourceWarning)

    app = aiohttp.web.Application()
    app.add_routes(h.get_routes())
    app.cleanup_ctx.append(background_tasks)
    aiohttp.web.run_app(app, port=8081)
    LOG.info("Shutting down...")


if __name__ == "__main__":
    main()
