import async_timeout
import asyncio

from hazard.thing import Thing, register_thing


DOUBLE_TAP_TIMEOUT = 0.4


class SwitchButtonBase:
  def __init__(self, switch):
    self._switch = switch
    self._code = {}

  def load_json(self, json):
    self._code.update(json.get('code', {}))

  def to_json(self):
    return {
      'type': type(self).__name__,
      'code': self._code,
    }


class SwitchBase(Thing):
  def __init__(self, hazard):
    super().__init__(hazard)
    self._buttons = []

  def load_json(self, json):
    super().load_json(json)
    self._buttons = []
    for b in json.get('buttons', []):
      btn = self._create_button()
      btn.load_json(b)
      self._buttons.append(btn)

  def _create_button(self):
    return None

  def to_json(self):
    json = super().to_json()
    json.update({
      'buttons': [b.to_json() for b in self._buttons],
    })
    return json

  def _features(self):
    return super()._features() + ['switch',]

  async def action(self, action, data):
    button = self._buttons[data.get('button', 0)]
    handler = getattr(button, 'action_' + action, None) or getattr(button, action, None)
    if handler:
      await handler()


class SwitchButton(SwitchButtonBase):
  def __init__(self, switch):
    super().__init__(switch)
    self._code = {
      'tap': '',
      'double_tap': '',
    }
    self._waiting_for_double = None

  async def action_tap(self):
    if not self._code['double_tap']:
      return await self.tap()

    if self._waiting_for_double:
      self._waiting_for_double.set_result(True)
      await self.double_tap()
      return

    self._waiting_for_double = asyncio.Future()

    try:
      async with async_timeout.timeout(DOUBLE_TAP_TIMEOUT):
        await self._waiting_for_double
    except asyncio.TimeoutError:
      await self.tap()
    finally:
      self._waiting_for_double.cancel()
      self._waiting_for_double = None

  async def tap(self):
    self._switch.execute(self._code['tap'])

  async def double_tap(self):
    self._switch.execute(self._code['double_tap'])


@register_thing
class Switch(SwitchBase):
  def __init__(self, hazard):
    super().__init__(hazard)

  def to_json(self):
    json = super().to_json()
    json.update({
    })
    return json

  def _create_button(self):
    return SwitchButton(self)


class StatefulSwitchButton(SwitchButtonBase):
  def __init__(self, switch):
    super().__init__(switch)
    self._code = {
      'on': '',
      'off': '',
      'toggle': '',
    }

  async def on(self):
    self._switch.execute(self._code['on'])

  async def off(self):
    self._switch.execute(self._code['off'])

  async def toggle(self):
    self._switch.execute(self._code['toggle'])


@register_thing
class StatefulSwitch(SwitchBase):
  def __init__(self, hazard):
    super().__init__(hazard)

  def to_json(self):
    json = super().to_json()
    json.update({
    })
    return json

  def _create_button(self):
    return StatefulSwitchButton(self)
