import json
import logging

from hazard.thing import register_thing
from hazard.things import Switch, SwitchButton

import zcl.spec

LOG = logging.getLogger('hazard')


@register_thing
class ZigBeeSwitch(Switch):
    def __init__(self, hazard):
        super().__init__(hazard)
        self._device = None

    async def _on_zcl(self, source_endpoint, dest_endpoint, cluster_name, command_type, command_name, **kwargs):
        #print('switch', source_endpoint, dest_endpoint, cluster_name, command_type, command_name, repr(kwargs))
        code = {
            'endpoint': source_endpoint,
            'cluster': cluster_name,
            'command': command_name,
            'args': kwargs,
        }
        await self.get_button(code).invoke()

    async def _on_announce(self):
        LOG.info('Auto-binding switch')
        coordinator_addr64 = await self._device._network._module.get_coordinator_addr64()

        endpoints = await self._device.zdo('active_ep', addr16=self._device.addr16())
        for ep in endpoints['active_eps']:
            simple_desc = await self._device.zdo('simple_desc', addr16=self._device.addr16(), endpoint=ep)
            desc = simple_desc['simple_descriptors'][0]
            clusters = desc['out_clusters']
            LOG.info('Discovered output clusters on endpoint {}: {}'.format(ep, clusters))

            onoff = zcl.spec.get_cluster_by_name('onoff')
            level = zcl.spec.get_cluster_by_name('level_control')
            for cluster in (onoff, level,):
                if cluster in clusters:
                    LOG.info('Binding {}'.format(cluster))
                    await self._device.zdo('bind',
                                                                  src_addr=self._device.addr64(),
                                                                  src_ep=ep,
                                                                  cluster=cluster,
                                                                  dst_addr_mode=3, # 64-bit device
                                                                  dst_addr=coordinator_addr64,
                                                                  dst_ep=1)

    async def create_from_device(self, device):
        self._device = device
        self._device.register_zcl(self._on_zcl)
        self._device.register_announce(self._on_announce)
        self._name = device._name

    def to_json(self):
        json = super().to_json()
        json.update({
            'device': self._device.addr64hex() if self._device else None,
        })
        return json

    def load_json(self, json):
        super().load_json(json)
        self._device = self._hazard.find_plugin('ZigBeePlugin').network().find_device(json['device'])
        self._device.register_zcl(self._on_zcl)
        self._device.register_announce(self._on_announce)

    def _create_button(self):
        return ZigBeeSwitchButton(self)
