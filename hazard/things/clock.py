from hazard.thing import Thing, register_thing

import asyncio

@register_thing
class Clock(Thing):
  def __init__(self, hazard):
    super().__init__(hazard)
    self._name = 'Clock'
    self._interval = 10
    self._code = ''
    loop = asyncio.get_event_loop()
    loop.create_task(self._tick())

  def _features(self):
    return super()._features() + ['clock']

  def load_json(self, json):
    super().load_json(json)
    self._interval = json.get('interval', 10)
    self._code = json.get('code', '')

  def to_json(self):
    json = super().to_json()
    json.update({
      'interval': self._interval,
      'code': self._code,
    })
    return json

  async def _tick(self):
    while True:
      await asyncio.sleep(self._interval)
      self._hazard.execute(self._code)      