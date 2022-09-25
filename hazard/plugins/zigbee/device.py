import asyncio
import async_timeout
import logging

from hazard.plugins.zigbee.common import ZigBeeDeliveryFailure, ZigBeeTimeout

import zcl.spec

LOG = logging.getLogger('hazard')

class ZigBeeDevice():
    def __init__(self, network, addr64=0, addr16=0, name=''):
        self._network = network
        self._addr64 = addr64
        self._addr16 = addr16
        self._name = name or 'Unknown {}'.format(self.addr64hex())
        if self._addr64:
            self._network._module.set_device_handler(self._addr64, self._on_frame)
        self._seq = 1
        self._inflight = {}
        self._on_zcl_callback = None
        self._on_announce_callback = None
        self._recent_seq = []

    def register_zcl(self, callback):
        self._on_zcl_callback = callback

    def register_announce(self, callback):
        self._on_announce_callback = callback

    def _on_frame(self, addr16, source_endpoint, dest_endpoint, cluster, profile, data):
        LOG.info("Frame ({}): {} {} {} {} {} {}".format(self._addr16, addr16, source_endpoint, dest_endpoint, cluster, profile, data))
        if addr16 != self._addr16:
            LOG.info('Updating addr16 on {} (rx: 0x{:04x}, config: 0x{:04x})'.format(self.addr64hex(), addr16, self._addr16))
            self._addr16 = addr16
            self._network._hazard.save()
        if profile == zcl.spec.Profile.ZIGBEE and dest_endpoint == zcl.spec.Endpoint.ZDO:
            self._on_zdo(cluster, data)
        else:
            self._on_zcl(source_endpoint, dest_endpoint, cluster, profile, data)

    def _on_zdo(self, cluster, data):
        cluster_name, seq, kwargs = zcl.spec.decode_zdo(cluster, data)
        LOG.info('ZDO from "{}" ({}): {} {}\n   {}'.format(self._name, self._addr16, seq, cluster_name, kwargs))
        if cluster_name == 'active_ep_resp':
                if 'active_eps' in kwargs and len(kwargs['active_eps']) == 0:
                        LOG.info('Fixing active eps')
                        kwargs['active_eps'].append(1)
                        kwargs['status'] = 0

        if seq in self._inflight:
            #print('  delivering future')
            self._inflight[seq].set_result(kwargs)
            return

        if cluster_name == 'match_desc':
            asyncio.get_event_loop().create_task(self._on_match_descriptors(**kwargs))
        elif cluster_name == 'device_annce':
            asyncio.get_event_loop().create_task(self._on_device_announce(**kwargs))

    def _on_zcl(self, source_endpoint, dest_endpoint, cluster, profile, data):
        cluster_name, seq, command_type, command_name, default_response, kwargs = zcl.spec.decode_zcl(cluster, data)
        LOG.info('ZCL from "{}": {} {} {} {} {} {} {} {} {}'.format(self._name, source_endpoint, dest_endpoint, seq, profile, cluster_name, command_type, command_name, default_response, kwargs))
        if seq in self._inflight:
            self._inflight[seq].set_result((command_name, kwargs,))
            return
        if seq in self._recent_seq:
            LOG.info('Ignoring duplicate ZCL')
            return
        self._recent_seq = self._recent_seq[-5:] + [seq]

        if default_response:
            asyncio.get_event_loop().create_task(self._send_default_response(source_endpoint, cluster_name, command_name, zcl.spec.Status.SUCCESS))
        if self._on_zcl_callback:
            asyncio.get_event_loop().create_task(self._on_zcl_callback(source_endpoint, dest_endpoint, cluster_name, command_type, command_name, **kwargs))


    async def _send_default_response(self, endpoint, cluster_name, command_name, status):
        # LOG.info('Sending default response to {} / {} / {} = {}'.format(endpoint, cluster_name, command_name, status))
        # _cluster, command, _args = zcl.spec.get_cluster_rx_command(cluster_name, command_name)
        # await self.zcl_profile(zcl.spec.Profile.HOME_AUTOMATION, endpoint, cluster_name, 'default_response', timeout=5, command=command, status=status)
        # Devices say they want a response but they're actually asleep.
        pass

    async def _on_match_descriptors(self, profile, in_clusters, addr16, out_clusters):
        if profile == zcl.spec.Profile.HOME_AUTOMATION and in_clusters == [0x0019]:
            # Ignore queries for the upgrade cluster.
            return
        LOG.warning('Attempted to match descriptors: profile {} / in {} / out {}'.format(profile, in_clusters, out_clusters))
        # Pretend like we support everything.
        LOG.info('Accepting match descriptor request')
        print(await self.zdo('match_desc_resp', status=0, addr16=0x0000, n_match_list=1, match_list=[1]))

    async def _on_device_announce(self, capability, addr64, addr16):
        if self._on_announce_callback:
            await self._on_announce_callback()
        #if self._addr64 == 3781220673614944:
        #    LOG.info('aanounce from multi')
        #    print('write attribute')
        #    print(await self.zcl_profile(0x0104, 1, 'ias_zone', 'write_attributes', attributes=[{'attribute': 0x0010, 'datatype': 'EUI64', 'value': await self._network._module.get_coordinator_addr64()}]))

                # print(await self.zcl_profile(0x0104, 1, 'ias_zone', 'configure_reporting', configs=[{'attribute': 0x0002, 'datatype': 'bitmap16', 'minimum': 0, 'maximum': 0, 'delta': 0 }]))

    def _next_seq(self):
        seq = self._seq
        self._seq = (self._seq + 1) % 256 or 1
        return seq

    async def _send(self, seq, source_endpoint, dest_endpoint, cluster, profile, data, timeout):
        if profile == zcl.spec.Profile.ZIGBEE_LIGHT_LINK:
            profile = zcl.spec.Profile.HOME_AUTOMATION

        f = asyncio.Future()
        self._inflight[seq] = f

            #print(hex(seq))
        result = await self._network._module.unicast(self._addr64, self._addr16, source_endpoint, dest_endpoint, cluster, profile, data)
        if not result:
            f.cancel()
            del self._inflight[seq]
            raise ZigBeeDeliveryFailure()

        try:
            async with async_timeout.timeout(timeout):
                return await f
        except asyncio.TimeoutError:
            raise ZigBeeTimeout() from None
        finally:
            del self._inflight[seq]

    async def zdo(self, cluster_name, timeout=10, **kwargs):
        seq = self._next_seq()
        cluster, data = zcl.spec.encode_zdo(cluster_name, seq, **kwargs)
        return await self._send(seq, 0, 0, cluster, zcl.spec.Profile.ZIGBEE, data, timeout)

    async def zcl_cluster(self, profile, dest_endpoint, cluster_name, command_name, timeout=5, **kwargs):
        seq = self._next_seq()
        cluster, data = zcl.spec.encode_cluster_command(cluster_name, command_name, seq, direction=0, default_response=True, **kwargs)
        return await self._send(seq, 1, dest_endpoint, cluster, profile, data, timeout)

    async def zcl_profile(self, profile, dest_endpoint, cluster_name, command_name, timeout=5, **kwargs):
        seq = self._next_seq()
        cluster, data = zcl.spec.encode_profile_command(cluster_name, command_name, seq, direction=0, default_response=True, **kwargs)
        print(data)
        return await self._send(seq, 1, dest_endpoint, cluster, profile, data, timeout)

    def addr64hex(self):
        return '0x{:08x}'.format(self._addr64)

    def addr16(self):
        return self._addr16

    def addr64(self):
        return self._addr64

    def to_json(self):
        return {
            'type': type(self).__name__,
            'addr64': self.addr64hex(),
            'addr16': self._addr16,
            'name': self._name,
        }

    def load_json(self, device_config):
        self._addr64 = int(device_config['addr64'], 16)
        self._addr16 = device_config['addr16']
        self._name = device_config.get('name', '')
        self._network._module.set_device_handler(self._addr64, self._on_frame)

    def update_from_json(self, device_config):
        if self._addr64 != int(device_config['addr64'], 16):
            raise ValueError('Updating from incorrect device')
        self._name = device_config.get('name', '')
