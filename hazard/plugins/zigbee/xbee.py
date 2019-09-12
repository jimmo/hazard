import asyncio
import async_timeout
import serial_asyncio
import struct
import logging

from hazard.plugins.zigbee.common import ZigBeeTimeout
from hazard.plugins.zigbee.module import ZigBeeModule

LOG = logging.getLogger('zigbee')

class XBeeProtocol(asyncio.Protocol):
  def __init__(self, xbee_module):
    self._xbee_module = xbee_module
    self._transport = None
    self._data = bytes()

  def connection_made(self, transport):
    self._transport = transport
    #print('port opened', transport)

  def data_received(self, data):
    #print('recv', data)
    self._data += data
    while self._find_frame():
      pass

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
    if not self._data:
      return False
    # Frames are: <1-byte 0x7e>, <2-byte length>, <data>, <1-byte checksum>
    i = 0
    if self._xbee_module._escape:
      if self._data[i] == 0x7e:
        len_bytes = bytearray()
        i += 1
        while len(len_bytes) < 2:
          if i >= len(self._data):
            return False
          if self._data[i] == 0x7d:
            len_bytes.append(0x20 ^ self._data[i+1],)
            i += 2
          else:
            len_bytes.append(self._data[i],)
            i += 1
        data_len, = struct.unpack('>H', len_bytes)
        frame = bytearray()
        while len(frame) < data_len:
          if i >= len(self._data):
            return False
          if self._data[i] == 0x7d:
            frame.append(0x20 ^ self._data[i+1],)
            i += 2
          else:
            frame.append(self._data[i],)
            i += 1

        chk_expected = self._checksum(frame)

        if i >= len(self._data):
          return False

        chk_actual = self._data[i]
        if chk_actual == 0x7d:
          i += 1
          chk_actual = 0x20 ^ self._data[i]
        i += 1
        if chk_expected == chk_actual:
          self._xbee_module._on_frame(frame)
        else:
          LOG.error('bad escape frame checksum at %d: %s from %s', i, frame, self._data[:i])
        self._data = self._data[i:]
        return True
    else:
      if self._data[i] == 0x7e:
        data_len, = struct.unpack('>H', self._data[i+1:i+3])
        frame_len = data_len + 4
        if i + frame_len > len(self._data):
          return False
        data = self._data[i + 3:i + frame_len - 1]
        chk = self._checksum(data)
        if chk == self._data[i + frame_len - 1]:
          self._xbee_module._on_frame(data)
        else:
          LOG.error('bad unescaped frame checksum at %d: %s', i, repr(data))
        self._data = self._data[i + frame_len:]
        return True
    return False

        # ~ \x00\x1e \x91\x00\x17\x88\x01\x04\n\x17\xf8\xb8\xb4\x00\x00\x00}3\x00\x00\x02\x00\xb4\xb8\xf8\x17\n\x04\x01\x88\x17\x00\x80\x87
        # ~ \x00\x1e \x91\x00\x17\x88\x01\x04\n\x17\xf8\xb8\xb4\x00\x00\x00}3\x00\x00\x02\x00\xb4\xb8\xf8\x17\n\x04\x01\x88\x17\x00\x80\x87


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
    self._escape = json.get('escape', False)

  def to_json(self):
    json = super().to_json()
    json.update({
      'port': self._port,
      'baudrate': self._baudrate,
      'escape': self._escape,
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
    return await self._tx_explicit(0xffffffffffffffff, group_addr, source_endpoint, dest_endpoint, cluster, profile, data, multicast=True, retries=False)

  async def broadcast(self, addr64, addr16, source_endpoint, dest_endpoint, cluster, profile, data):
    return await self._tx_explicit(0x000000000000ffff, 0xffff, source_endpoint, dest_endpoint, cluster, profile, data)

  async def allow_joining(self, allow):
    await self._send_at('NJ', 0xff if allow else 0)
    result = await self._send_at('NJ')
    LOG.warning('Allow joining: %s', result > 0)

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
    #print('tx explicit ', hex(addr64), hex(addr16))
    response = await self._send_frame(0x11, data, status=not multicast)
    #print('tx explicit response ', hex(addr64), hex(addr16))
    #print(response)
    sent_addr16, retry_count, delivery_status, discovery_status, = struct.unpack('>HBBB', response)
    #print('tx response', sent_addr16, retry_count, delivery_status, discovery_status)
    #return True
    return delivery_status == 0

  def _on_frame(self, data):
    if len(data) < 2:
      LOG.error('Frame too small')
      return
    #print('recv', data)
    frame_type, = struct.unpack('B', data[:1])
    data = data[1:]

    self._rx = True

    if frame_type in (0x88, 0x8b,):
      # AT Response or Transmit Status
      frame_id, = struct.unpack('B', data[:1])
      data = data[1:]
      if frame_id in self._inflight:
        self._inflight[frame_id].set_result(data)
      else:
        LOG.error('Reply for unknown frame id: 0x{:02x}'.format(frame_id))
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
        LOG.error('Error in device frame handler')
        LOG.error(traceback.format_exc())
    else:
      LOG.error('Unknown frame type: 0x{:02x}'.format(frame_type,))

  async def _send_frame(self, frame_type, data, timeout=5, status=True):
    #while self._rx:
    #  self._rx = False
    #  await asyncio.sleep(0.1)

    # while len(self._inflight) > 1:
    #   await asyncio.sleep(0.1)

    if status:
      frame_id = self._frame_id
      self._frame_id = (self._frame_id + 1) % 256 or 1
    else:
      frame_id = 0

    data = struct.pack('BB', frame_type, frame_id) + data
    if self._escape:
      checksum = struct.pack('B', self._protocol._checksum(data))
      data = struct.pack('>H', len(data)) + data
      escaped_data = bytearray()
      for b in data:
        if b in (0x7d, 0x73, 0x11, 0x13,):
          escaped_data.append(0x7d)
          escaped_data.append(0x20 ^ b)
        else:
          escaped_data.append(b)
      data = b'\x7e' + escaped_data + checksum
    else:
      data = b'\x7e' + struct.pack('>H', len(data)) + data + struct.pack('B', self._protocol._checksum(data))
    #print('sending', data)

    if status:
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
    else:
      self._protocol._transport.write(data)
      return struct.pack('>HBBB', 0xfffd, 0, 0, 0)

  async def _send_at(self, command, val=None):
    t = STRUCT_TYPES[AT_COMMANDS[command]]
    req = command.encode()
    if val is not None:
      req += struct.pack(t, val)
    resp = await self._send_frame(0x08, req)
    if resp[0:2] != req[0:2]:
      LOG.error('Unexpected AT response: resp=%s, req=%s', repr(resp), repr(req))
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
        LOG.debug('Ping response', hex(result))
      except ZigBeeTimeout:
        LOG.debug('Ping timeout')
