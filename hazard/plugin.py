PLUGINS = {}


def register_plugin(cls):
    PLUGINS[cls.__name__] = cls
    return cls


def create_plugin(json, hazard):
    plugin = PLUGINS[json['type']](hazard)
    plugin.load_json(json)
    return plugin


class HazardPlugin:
    def __init__(self, hazard):
        self._hazard = hazard

    def load_json(self, json):
        pass

    def to_json(self):
        return {
            'type': type(self).__name__
        }

    def get_routes(self):
        return []

    async def start(self):
        pass

    async def stop(self):
        pass
