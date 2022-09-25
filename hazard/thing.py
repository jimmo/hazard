import logging

THINGS = {}

LOG = logging.getLogger('hazard')


def register_thing(cls):
    THINGS[cls.__name__] = cls
    return cls


def create_thing_from_json(json, hazard):
    thing = THINGS[json['type']](hazard)
    thing.load_json(json)
    return thing


def create_thing(cls, hazard):
    if not isinstance(cls, str):
        cls = cls.__name__
    thing = THINGS[cls](hazard)
    return thing


def get_thing_types():
    return THINGS.keys()


class ThingLocation:
    def __init__(self):
        self.x = 0
        self.y = 0

    def to_json(self):
        return {
            'type': type(self).__name__,
            'x': self.x,
            'y': self.y,
        }

    def load_json(self, json):
        self.x = json.get('x', 0)
        self.y = json.get('y', 0)


class Thing:
    def __init__(self, hazard):
        self._hazard = hazard
        self._id = None
        self._name = '(unknown)'
        self._zone = 'Home'
        self._location = { 'x': 0, 'y': 0 }

    def load_json(self, json):
        self._id = json.get('id', None)
        self._name = json.get('name', '(unknown)')
        self._zone = json.get('zone', 'Home')
        self._location = json.get('location', {'x': 0, 'y': 0})

    def to_json(self):
        return {
            'type': type(self).__name__,
            'json_type': 'Thing',
            'id': self._id,
            'name': self._name,
            'zone': self._zone,
            'features': self._features(),
            'location': self._location,
        }

    def id(self):
        return self._id

    def name(self):
        return self._name

    def zone(self):
        return self._zone

    def _features(self):
        return []

    async def action(self, action, data):
        await getattr(self, action)(**data)

    def remove(self):
        self._hazard.remove_thing(self)

    async def reconfigure(self):
        LOG.info('Reconfigure "%s"', self.name())

    async def start(self):
        pass

    async def stop(self):
        pass
