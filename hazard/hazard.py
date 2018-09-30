import aiohttp.web
import json

from hazard.thing import create_thing, create_thing_from_json
import hazard.things

from hazard.plugin import create_plugin
import hazard.plugins

from hazard.action import Action


class Hazard:
  def __init__(self):
    self._plugins = {}
    self._zones = {}
    self._things = {}
    self._actions = {}
    self._tseq = 10
    self._aseq = 1

  def load(self):
    #try:
    with open('/home/jimmo/.hazard', 'r') as f:
      config = json.load(f)
      for p in config.get('plugins', []):
        print('Plugin: {}'.format(p))
        p = create_plugin(p, self)
        self._plugins[type(p).__name__] = p
      for t in config.get('things', []):
        print('Thing: {}'.format(t))
        t = create_thing_from_json(t, self)
        self._tseq = max(t.id() + 1, self._tseq)
        self._things[t.id()] = t
      for a in config.get('actions', []):
        print('Action: {}'.format(t))
        action = Action(self)
        action.load_json(a)
        self._aseq = max(action.id() + 1, self._aseq)
        self._actions[action.id()] = action
    #except FileNotFoundError:
    #  pass
    #except json.decoder.JSONDecodeError:
    #  pass

    if 'RestPlugin' not in self._plugins:
      print('Creating default rest plugin')
      self._plugins['RestPlugin'] = hazard.plugins.RestPlugin(self)
    if 'AppPlugin' not in self._plugins:
      print('Creating default app plugin')
      self._plugins['AppPlugin'] = hazard.plugins.AppPlugin(self)
      
    #self.save()

  def save(self):
    with open('/home/jimmo/.hazard', 'w') as f:
      config = {
        'plugins': [
          p.to_json() for p in self._plugins.values()
        ],
        'things': [
          t.to_json() for t in self._things.values()
        ],
        'actions': [
          a.to_json() for a in self._actions.values()
        ],
      }
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
    return [
    ] + sum([p.get_routes() for p in self._plugins.values()], [])


  async def reconfigure(self):
    for thing in self._things.values():
      await thing.reconfigure()
      
  def create_action(self):
    action = Action(self)
    action._id = self._aseq
    self._aseq += 1
    self._actions[action.id()] = action
    return action

  
  def execute(self, code):
    if not code:
      return
    
    code = 'async def __code():\n  import asyncio\n' + '\n'.join('  ' + line for line in code.split('\n')) + '\n\nimport asyncio\nasyncio.get_event_loop().create_task(__code())\n'
    exec(code, {
      'action': self.find_action,
      'thing': self.find_thing,
    }, {
      'self': self,
    })
