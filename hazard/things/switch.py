import async_timeout
import asyncio
import json
import logging

from hazard.thing import Thing, register_thing


DOUBLE_TAP_TIMEOUT = 0.4

LOG = logging.getLogger('hazard')


class SwitchButton:
  def __init__(self, switch, code={}):
    self._switch = switch
    self._name = code
    self._code = code
    self._tap = ''
    self._single = ''
    self._double = ''
    self._waiting_for_double = None

  def load_json(self, obj):
    self._name = obj.get('name', '')
    self._code = obj.get('code', {})
    if isinstance(self._code, str):
      self._code = json.loads(self._code)
    self._tap = obj.get('tap', '')
    self._single = obj.get('single', '')
    self._double = obj.get('double', '')

  def to_json(self):
    return {
      'type': type(self).__name__,
      'json_type': 'SwitchButton',
      'code': self._code,
      'name': self._name,
      'tap': self._tap,
      'single': self._single,
      'double': self._double,
    }

  def name(self):
    return self._name

  def code(self):
    return self._code

  async def invoke(self):
    LOG.info('Invoking "%s/%s"', self._switch._name, self._name)
    if not self._double:
      if await self.tap():
        return await self.single()

    if self._waiting_for_double:
      self._waiting_for_double.set_result(True)
      await self.double()
      return

    self._waiting_for_double = asyncio.Future()

    try:
      async with async_timeout.timeout(DOUBLE_TAP_TIMEOUT):
        if await self.tap():
          await self._waiting_for_double
    except asyncio.TimeoutError:
      await self.single()
    finally:
      if self._waiting_for_double:
        self._waiting_for_double.cancel()
      self._waiting_for_double = None

  async def tap(self):
    LOG.info('Tap on "%s/%s"', self._switch._name, self._name)
    return await self._switch._hazard.execute(self._tap)

  async def single(self):
    LOG.info('Single tap on "%s/%s"', self._switch._name, self._name)
    return await self._switch._hazard.execute(self._single)

  async def double(self):
    LOG.info('Double tap on "%s/%s"', self._switch._name, self._name)
    return await self._switch._hazard.execute(self._double)


@register_thing
class Switch(Thing):
  def __init__(self, hazard):
    super().__init__(hazard)
    self._buttons = []

  def load_json(self, obj):
    super().load_json(obj)
    self._buttons = []
    for b in obj.get('buttons', []):
      btn = SwitchButton(self)
      btn.load_json(b)
      self._buttons.append(btn)

  def to_json(self):
    obj = super().to_json()
    obj.update({
      'json_type': 'Switch',
      'buttons': [b.to_json() for b in self._buttons],
    })
    return obj

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
