import aiohttp.web
import json
import datetime
import logging
import urllib.request
import collections

from hazard.thing import create_thing, create_thing_from_json
import hazard.things

from hazard.plugin import create_plugin
import hazard.plugins

from hazard.action import Action

LOG = logging.getLogger("hazard")


class Hazard:
    def __init__(self):
        self._plugins = {}
        self._zones = {}
        self._things = {}
        self._actions = {}
        self._tseq = 10
        self._aseq = 1
        self._state = collections.defaultdict(lambda: None)

    def load(self):
        # try:
        with open("/home/jimmo/.hazard", "r") as f:
            config = json.load(f)
            for p in config.get("plugins", []):
                LOG.debug("Plugin: {}".format(p))
                p = create_plugin(p, self)
                self._plugins[type(p).__name__] = p
            for t in config.get("things", []):
                LOG.debug("Thing: {}".format(t))
                t = create_thing_from_json(t, self)
                self._tseq = max(t.id() + 1, self._tseq)
                self._things[t.id()] = t
            for a in config.get("actions", []):
                LOG.debug("Action: {}".format(a))
                action = Action(self)
                action.load_json(a)
                self._aseq = max(action.id() + 1, self._aseq)
                self._actions[action.id()] = action
            self._state.update(config.get("state", {}))
        # except FileNotFoundError:
        #  pass
        # except json.decoder.JSONDecodeError:
        #  pass

        if "RestPlugin" not in self._plugins:
            LOG.warning("Creating default rest plugin")
            self._plugins["RestPlugin"] = hazard.plugins.RestPlugin(self)
            self.save()
        if "AppPlugin" not in self._plugins:
            LOG.warning("Creating default app plugin")
            self._plugins["AppPlugin"] = hazard.plugins.AppPlugin(self)
            self.save()

    async def start(self):
        for p in self._plugins.values():
            await p.start()
        for t in self._things.values():
            await t.start()

    async def stop(self):
        for p in self._plugins.values():
            await p.stop()
        for t in self._things.values():
            await t.stop()

    def save(self):
        config = {
            "plugins": [p.to_json() for p in self._plugins.values()],
            "things": [t.to_json() for t in self._things.values()],
            "actions": [a.to_json() for a in self._actions.values()],
            "state": self._state,
        }
        with open("/home/jimmo/.hazard", "w") as f:
            json.dump(config, f, indent=2)

    def find_plugin(self, cls):
        if not isinstance(cls, str):
            cls = cls.__name__
        return self._plugins[cls]

    def find_thing(self, name):
        for t in self._things.values():
            if t.name() == name:
                return t
        raise ValueError('Thing "{}" not found'.format(name))

    def all_things(self):
        return self._things.values()

    def find_things(self, thing_type):
        return [t for t in self._things.values() if isinstance(t, thing_type)]

    def find_action(self, name):
        for a in self._actions.values():
            if a.name() == name:
                return a
        raise ValueError('Action "{}" not found'.format(name))

    def remove_thing(self, thing):
        del self._things[thing.id()]
        self.save()

    def create_thing(self, cls):
        thing = create_thing(cls, self)
        thing._id = self._tseq
        self._tseq += 1
        self._things[thing.id()] = thing
        return thing

    def get_routes(self):
        return [] + sum([p.get_routes() for p in self._plugins.values()], [])

    async def reconfigure(self):
        for thing in self._things.values():
            try:
                await thing.reconfigure()
            except:
                pass

    def create_action(self):
        action = Action(self)
        action._id = self._aseq
        self._aseq += 1
        self._actions[action.id()] = action
        return action

    async def http_get(self, url):
        req = urllib.request.Request(url, headers=headers, data=data, method="GET")
        try:
            urllib.request.urlopen(req)
        except:
            pass

    async def http_post(self, url, headers={}, data=None):
        req = urllib.request.Request(url, headers=headers, data=data, method="POST")
        try:
            urllib.request.urlopen(req)
        except:
            pass

    async def execute(self, code):
        if not code.strip():
            return True

        LOG.debug("Executing code:\n%s", code)

        code = (
            """
import asyncio
async def __code():
    import sys
    import asyncio
    import datetime
    import time
    import os

    result = True

    def cancel():
        nonlocal result
        result = False

    try:
"""
            + "\n".join("        " + line for line in code.split("\n"))
            + """
    except Exception as e:
        import sys
        t, v, tb = sys.exc_info()
        import logging
        import traceback
        logging.getLogger('hazard').error("Error in event handler: {}: {}\\n{}".format(t.__name__, v, ''.join(traceback.format_tb(tb))))

    return result

self._exec_task = asyncio.get_event_loop().create_task(__code())
"""
        )

        exec(
            code,
            {
                "action": self.find_action,
                "thing": self.find_thing,
                "things": self.all_things,
                "state": self._state,
                "hour": lambda: datetime.datetime.now().hour,
                "minute": lambda: datetime.datetime.now().minute,
                "http_get": self.http_get,
                "http_post": self.http_post,
                "hazard": self,
            },
            {
                "self": self,
            },
        )

        return await self._exec_task
