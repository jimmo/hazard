import async_timeout
import asyncio

from hazard.thing import Thing, register_thing


DOUBLE_TAP_TIMEOUT = 0.4


class SwitchButton:
  def __init__(self, switch, code=''):
    self._switch = switch
    self._name = code
    self._code = code
    self._single = ''
    self._double = ''
    self._waiting_for_double = None

  def load_json(self, json):
    self._name = json.get('name', '')
    self._code = json.get('code', '')
    self._single = json.get('single', '')
    self._double = json.get('double', '')

  def to_json(self):
    return {
      'type': type(self).__name__,
      'json_type': 'SwitchButton',
      'code': self._code,
      'name': self._name,
      'single': self._single,
      'double': self._double,
    }

  def name(self):
    return self._name

  def code(self):
    return self._code
    
  async def invoke(self):
    if not self._double:
      return await self.single()

    if self._waiting_for_double:
      self._waiting_for_double.set_result(True)
      await self.double()
      return

    self._waiting_for_double = asyncio.Future()

    try:
      async with async_timeout.timeout(DOUBLE_TAP_TIMEOUT):
        await self._waiting_for_double
    except asyncio.TimeoutError:
      await self.single()
    finally:
      self._waiting_for_double.cancel()
      self._waiting_for_double = None

  async def single(self):
    self._switch.execute(self._single)

  async def double(self):
    self._switch.execute(self._double)


@register_thing
class Switch(Thing):
  def __init__(self, hazard):
    super().__init__(hazard)
    self._buttons = []

  def load_json(self, json):
    super().load_json(json)
    self._buttons = []
    for b in json.get('buttons', []):
      btn = SwitchButton(self)
      btn.load_json(b)
      self._buttons.append(btn)

  def to_json(self):
    json = super().to_json()
    json.update({
      'json_type': 'Switch',
      'buttons': [b.to_json() for b in self._buttons],
    })
    return json

  def _features(self):
    return super()._features() + ['switch',]

  def get_button(self, code, create=True):
    for btn in self._buttons:
      if btn.code() == code:
        return btn
    if create:
      btn = SwitchButton(self, code)
      self._buttons.append(btn)
      self._hazard.save()
      return btn
    else:
      return None

  async def action(self, action, data):
    btn = self.get_button(data.get('code', ''))
    if not btn:
      return
    if action == 'invoke':
      await btn.invoke()
    elif action == 'single':
      await btn.single()
    elif action == 'double':
      await btn.double()
