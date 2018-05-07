import aiohttp.web
import json

from hazard.thing import create_thing, create_thing_from_json
import hazard.things

from hazard.plugin import create_plugin
import hazard.plugins


class Hazard:
  def __init__(self):
    self._plugins = {}
    self._zones = {}
    self._things = {}
    self._seq = 10

  def load(self):
    #try:
    with open('/home/jimmo/.hazard', 'r') as f:
      config = json.load(f)
      for p in config.get('plugins', []):
        print('Plugin: {}'.format(p))
        p = create_plugin(p, self)
        self._plugins[type(p).__name__] = p
      for z in config.get('zones', []):
        print('Zone: {}'.format(z))
      for t in config.get('things', []):
        print('Thing: {}'.format(t))
        t = create_thing_from_json(t, self)
        self._seq = max(t.id() + 1, self._seq)
        self._things[t.id()] = t
    #except FileNotFoundError:
    #  pass
    #except json.decoder.JSONDecodeError:
    #  pass

    if 'RestPlugin' not in self._plugins:
      print('Creating default rest plugin')
      self._plugins['RestPlugin'] = hazard.plugins.RestPlugin(self)
    if 'WebPlugin' not in self._plugins:
      print('Creating default web plugin')
      self._plugins['WebPlugin'] = hazard.plugins.WebPlugin(self)

    # if 1 not in self._things:
    #   s = hazard.things.Switch(self)
    #   s._id = 1
    #   s._name = 'Switch 1'
    #   #s.add_button('print("a")')
    #   #s.add_button('print("b")')
    #   #s.add_button('print("c")')
    #   self._things[s.id()] = s

    # if 2 not in self._things:
    #   l1 = hazard.things.Light(self)
    #   l1._id = 2
    #   l1._name = 'Light 1'
    #   self._things[l1.id()] = l1

    # if 3 not in self._things:
    #   l2 = hazard.things.Light(self)
    #   l2._id = 3
    #   l2._name = 'Light 2'
    #   self._things[l2.id()] = l2

    # if 4 not in self._things:
    #   g1 = hazard.things.LightGroup(self)
    #   g1._id = 4
    #   g1._name = 'Group 1'
    #   self._things[g1.id()] = g1

    # if 5 not in self._things:
    #   zl = hazard.plugins.zigbee.things.ZigBeeLight(self)

    #self.save()

  def save(self):
    with open('/home/jimmo/.hazard', 'w') as f:
      config = {
        'plugins': [
          p.to_json() for p in self._plugins.values()
        ],
        'zones': [
          z.to_json() for z in self._zones.values()
        ],
        'things': [
          t.to_json() for t in self._things.values()
        ],
      }
      json.dump(config, f, indent=2)

  def find_plugin(self, cls):
    if not isinstance(cls, str):
      cls = cls.__name__
    return self._plugins[cls]

  def find_zone(self, name):
    return None

  def find_thing(self, name):
    for t in self._things.values():
      if t.name() == name:
        return t
    raise ValueError('Thing "{}" not found'.format(name))

  def create_thing(self, cls):
    thing = create_thing(cls, self)
    thing._id = self._seq
    self._seq += 1
    self._things[thing.id()] = thing
    return thing

  def get_routes(self):
    return [
      aiohttp.web.get('/js/{plugin}/{file}.js', self.handle_js),
      aiohttp.web.get('/css/{plugin}/{file}.css', self.handle_css),
      aiohttp.web.get('/riot/{plugin}/{file}.tag', self.handle_riot),
    ] + sum([p.get_routes() for p in self._plugins.values()], [])

  async def handle_js(self, request):
    return aiohttp.web.FileResponse('hazard/plugins/{}/js/{}.js'.format(request.match_info['plugin'], request.match_info['file']))

  async def handle_css(self, request):
    return aiohttp.web.FileResponse('hazard/plugins/{}/css/{}.css'.format(request.match_info['plugin'], request.match_info['file']))

  async def handle_riot(self, request):
    return aiohttp.web.FileResponse('hazard/plugins/{}/riot/{}.tag'.format(request.match_info['plugin'], request.match_info['file']))
