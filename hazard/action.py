class Action:
  def __init__(self, hazard):
    self._hazard = hazard
    self._id = None
    self._name = '(unknown)'
    self._code = ''

  def id(self):
    return self._id

  def name(self):
    return self._name

  def load_json(self, json):
    self._id = json.get('id', self._id)
    self._name = json.get('name', self._name)
    self._code = json.get('code', self._code)

  def to_json(self):
    return {
      'type': type(self).__name__,
      'json_type': 'Action',
      'id': self._id,
      'name': self._name,
      'code': self._code,
    }

  def remove(self):
    del self._hazard._actions[self._id]
    self._hazard.save()

  def invoke(self, data=None):
    self._hazard.execute(self._code)

