THINGS = {}


def register_thing(cls):
  THINGS[cls.__name__] = cls
  return cls


def create_thing(json, hazard):
  thing = THINGS[json['type']](hazard)
  thing.load_json(json)
  return thing


class ThingBase:
  def __init__(self, hazard):
    self._hazard = hazard
    self._id = None
    self._name = None
    self._zone = None
    self._location = { 'x': 0, 'y': 0 }


  def load_json(self, json):
    self._id = json.get('id', None)
    self._name = json.get('name', '(unknown)')
    self._zone = self._hazard.find_zone(json.get('zone', None))
    self._location = json.get('location', {'x': 0, 'y': 0})

  def to_json(self):
    return {
      'type': type(self).__name__,
      'id': self._id,
      'name': self._name,
      'zone': self._zone.name() if self._zone else None,
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

  def execute(self, code):
    exec(code, {
      'thing': self._hazard.find_thing,
    }, {
      'self': self,
    })

  async def action(self, action, data):
    await getattr(self, action)(**data)


class Thing(ThingBase):
  def __init__(self, hazard):
    super().__init__(hazard)

  def load_json(self, json):
    super().load_json(json)

  def to_json(self):
    json = super().to_json()
    json.update({})
    return json


class ThingGroup(ThingBase):
  def __init__(self, hazard):
    super().__init__(hazard)
    self._size = { 'w': 100, 'h': 100 }

  def load_json(self, json):
    super().load_json(json)
    self._size = json.get('size', {'w': 100, 'h': 100})

  def to_json(self):
    json = super().to_json()
    json.update({
      'size': self._size,
    })
    return json

  def _features(self):
    return ['group']
