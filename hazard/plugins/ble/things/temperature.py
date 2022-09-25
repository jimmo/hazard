import datetime
import logging
import struct

from hazard.thing import register_thing
from hazard.things import Temperature

LOG = logging.getLogger("hazard")


@register_thing
class BleTemperature(Temperature):
    def __init__(self, hazard):
        super().__init__(hazard)
        self._ble_adv_name = None

    def to_json(self):
        json = super().to_json()
        json.update(
            {
                "ble_adv_name": self._ble_adv_name,
            }
        )
        return json

    def _on_update(self, device, manuf):
        if len(manuf) != 4:
            return
        h, t = struct.unpack("<hh", bytes(manuf))
        self._temperature = t / 8
        self._humidity = h / 2
        self._last_update = int(datetime.datetime.now().timestamp())
        LOG.info(
            "Temp update,%d,%s,%s,%f,%f",
            device.rssi,
            self._ble_adv_name,
            self._name,
            h / 2,
            t / 8,
        )

    def load_json(self, json):
        super().load_json(json)
        self._ble_adv_name = json.get("ble_adv_name", None)
        if self._ble_adv_name:
            ble = self._hazard.find_plugin("BlePlugin")
            ble.register_advertisement(self._ble_adv_name, self._on_update)
