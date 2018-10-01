import asyncio
import async_timeout
import serial_asyncio
import struct

from hazard.plugins.zigbee.common import ZigBeeTimeout
from hazard.plugins.zigbee.module import ZigBeeModule


class XBeeProtocol(asyncio.Protocol):
  def __init__(self, xbee_module):
    self._xbee_module = xbee_module
    self._transport = None
    self._data = bytes()

  def connection_made(self, transport):
    self._transport = transport
    #print('port opened', transport)

  def data_received(self, data):
    self._data += data
    self._find_frame()

  def connection_lost(self, exc):
    print('port closed')
    #self.transport.loop.stop()

  def pause_writing(self):
    print('pause writing')
    print(self._transport.get_write_buffer_size())

  def resume_writing(self):
    print(self._transport.get_write_buffer_size())
    print('resume writing')

  def _checksum(self, data):
    chk = 0
    for b in data:
      chk += b
    return 0xff - (chk & 0xff)

  def _find_frame(self):
    # Frames are: <1-byte 0x7e>, <2-byte length>, <data>, <1-byte checksum>
    i = 0
    while i < len(self._data) - 3:
      if self._data[i] == 0x7e:
        data_len, = struct.unpack('>H', self._data[i+1:i+3])
        frame_len = data_len + 4
        if i + frame_len < len(self._data):
          continue
        data = self._data[i + 3:i + frame_len - 1]
        chk = self._checksum(data)
        if len(self._data) > i + frame_len - 1 and chk == self._data[i + frame_len - 1]:
          self._xbee_module._on_frame(data)
        else:
          print('bad frame', data)
        self._data = self._data[i + frame_len:]
        i = 0


STRUCT_TYPES = {
  'uint8': '>B',
  'uint16': '>H',
  'uint32': '>I',
  'uint64': '>Q',
  'int8': '>b',
  'int16': '>h',
  'int32': '>i',
  'int64': '>q',
}


AT_COMMANDS = {
  'OP': 'uint64',
  'SH': 'uint32',
  'SL': 'uint32',
  'NC': 'uint8',
  'NJ': 'uint8',
}


class XBeeModule(ZigBeeModule):
  def __init__(self):
    super().__init__()
    self._protocol = None
    self._frame_id = 27
    self._inflight = {}
    self._port = ''
    self._baudrate = 0
    self._rx = False

  def load_json(self, json):
    super().load_json(json)
    self._port = json.get('port', '')
    self._baudrate = json.get('baudrate', 0)
    self.connect()

  def to_json(self):
    json = super().to_json()
    json.update({
      'port': self._port,
      'baudrate': self._baudrate,
    })
    return json

  def _create_protocol(self):
    self._protocol = XBeeProtocol(self)
    return self._protocol

  def connect(self):
    if not self._port or not self._baudrate:
      return
    loop = asyncio.get_event_loop()
    coro = serial_asyncio.create_serial_connection(loop, self._create_protocol, self._port, baudrate=self._baudrate)
    loop.create_task(coro)
    #loop.create_task(self._ping())

  async def get_coordinator_addr64(self):
    sh = await self._send_at('SH')
    sl = await self._send_at('SL')
    return (sh << 32) + sl

  async def get_pan_id(self):
    return await self._send_at('OP')

  async def unicast(self, addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data):
    return await self._tx_explicit(addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data)

  async def multicast(self, group_addr, source_endpoint, dest_endpoint, cluster, profile, data):
    return await self._tx_explicit(0xffffffffffffffff, group_addr, source_endpoint, dest_endpoint, cluster, profile, data, multicast=True)

  async def broadcast(self, addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data):
    return await self._tx_explicit(0x000000000000ffff, 0xffff, source_endpoint, dest_endpoint, cluster, profile, data)

  async def allow_joining(self, allow):
    await self._send_at('NJ', 0xff if allow else 0)
    result = await self._send_at('NJ')
    print('Allow joining: ', result > 0)

  async def _tx_explicit(self, addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data, radius=0, retries=True, indirect=False, multicast=False, aps=False, extended_timeout=False):
    opt = 0
    if not retries:
      opt |= 0x01
    if indirect:
      opt |= 0x04
    if multicast:
      opt |= 0x08
    if aps:
      opt |= 0x20
    if extended_timeout:
      opt |= 0x40
    data = struct.pack('>QHBBHHBB', addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, radius, opt) + data
    response = await self._send_frame(0x11, data)
    #print(response)
    sent_addr16, retry_count, delivery_status, discovery_status, = struct.unpack('>HBBB', response)
    #print('tx response', sent_addr16, retry_count, delivery_status, discovery_status)
    #return True
    return delivery_status == 0

  def _on_frame(self, data):
    if len(data) < 2:
      print('Frame too small')
      return
    #print(data)
    frame_type, = struct.unpack('B', data[:1])
    data = data[1:]

    self._rx = True

    if frame_type in (0x88, 0x8b,):
      # AT Response or Transmit Status
      frame_id, = struct.unpack('B', data[:1])
      data = data[1:]
      if frame_id in self._inflight:
        self._inflight[frame_id].set_result(data)
    elif frame_type == 0x91:
      # Explicit RX Indicator Frame
      addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, opt = struct.unpack('>QHBBHHB', data[:17])
      data = data[17:]
      ack = not not (opt & 0x01)
      broadcast = not not (opt & 0x02)
      aps = not not (opt & 0x20)
      #print(ack, broadcast, aps)
      try:
        self._on_device_frame(addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data)
      except Exception as e:
        import traceback
        print('Error in device frame handler')
        print(traceback.print_exc())
    else:
      print('Unknown frame type: 0x{:02x}'.format(frame_type,))

  async def _send_frame(self, frame_type, data, timeout=5, reply=True):
    #while self._rx:
    #  self._rx = False
    #  await asyncio.sleep(0.1)
      
    # while len(self._inflight) > 2:
    #   await asyncio.sleep(0.1)

    data = struct.pack('BB', frame_type, self._frame_id) + data
    data = b'\x7e' + struct.pack('>H', len(data)) + data + struct.pack('B', self._protocol._checksum(data))
    frame_id = self._frame_id
    self._frame_id = (self._frame_id + 1) % 256 or 1

    f = asyncio.Future()
    #print(len(self._inflight))
    self._inflight[frame_id] = f
    #print('frame', data)
    self._protocol._transport.write(data)
    try:
      async with async_timeout.timeout(timeout):
        return await f
    except asyncio.TimeoutError:
      raise ZigBeeTimeout() from None
    finally:
      del self._inflight[frame_id]

  async def _send_at(self, command, val=None):
    t = STRUCT_TYPES[AT_COMMANDS[command]]
    req = command.encode()
    if val is not None:
      req += struct.pack(t, val)
    resp = await self._send_frame(0x08, req)
    if resp[0:2] != req[0:2]:
      print('Unexpected AT response')
    if resp[2] != 0x00:
      raise ValueError('Invalid AT request')
    else:
      if len(resp) > 3:
        return struct.unpack(t, resp[3:])[0]
      else:
        return None

  async def _ping(self):
    while True:
      for i in range(50):
        await asyncio.sleep(0.1)
      try:
        result = await self._send_at('NC')
        print('Ping response', hex(result))
      except ZigBeeTimeout:
        print('Ping timeout')
      #await self._tx_explicit(1403434233899801417, 63488, 1, 1, )
