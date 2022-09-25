import asyncio
import async_timeout

from hazard.plugins.zigbee.common import ZigBeeDeliveryFailure, ZigBeeTimeout

import zcl.spec


class ZigBeeGroup:
    def __init__(self, network, addr16=0, name=""):
        self._network = network
        self._addr16 = addr16
        self._name = name
        self._seq = 127

    def to_json(self):
        return {
            "type": type(self).__name__,
            "addr16": self._addr16,
            "name": self._name,
        }

    def load_json(self, group_config):
        self._addr16 = group_config.get("addr16", 0)
        self._name = group_config.get("name", "")

    def update_from_json(self, group_config):
        if self._addr16 != group_config["addr16"]:
            raise ValueError("Updating from incorrect group")
        self._name = group_config.get("name", "")

    def _next_seq(self):
        seq = self._seq
        self._seq = (self._seq + 1) % 256 or 1
        return seq

    async def _send(
        self, seq, source_endpoint, dest_endpoint, cluster, profile, data, timeout
    ):
        if profile == zcl.spec.Profile.ZIGBEE_LIGHT_LINK:
            profile = zcl.spec.Profile.HOME_AUTOMATION

        result = await self._network._module.multicast(
            self._addr16, source_endpoint, dest_endpoint, cluster, profile, data
        )
        if not result:
            raise ZigBeeDeliveryFailure()

    async def zdo(self, cluster_name, timeout=10, **kwargs):
        seq = self._next_seq()
        cluster, data = zcl.spec.encode_zdo(cluster_name, seq, **kwargs)
        return await self._send(
            seq, 0, 0, cluster, zcl.spec.Profile.ZIGBEE, data, timeout
        )

    async def zcl_cluster(
        self, profile, dest_endpoint, cluster_name, command_name, timeout=5, **kwargs
    ):
        seq = self._next_seq()
        cluster, data = zcl.spec.encode_cluster_command(
            cluster_name,
            command_name,
            seq,
            direction=0,
            default_response=False,
            **kwargs
        )
        return await self._send(seq, 1, dest_endpoint, cluster, profile, data, timeout)

    async def zcl_profile(
        self, profile, dest_endpoint, cluster_name, command_name, timeout=5, **kwargs
    ):
        seq = self._next_seq()
        cluster, data = zcl.spec.encode_profile_command(
            cluster_name,
            command_name,
            seq,
            direction=0,
            default_response=False,
            **kwargs
        )
        return await self._send(seq, 1, dest_endpoint, cluster, profile, data, timeout)

    def find_member_things(self, thing_type):
        return [
            t
            for t in self._network._hazard.find_things(thing_type)
            if self._addr16 in t._groups
        ]

    def get_thing(self, thing_group_type):
        for t in self._network._hazard.find_things(thing_group_type):
            if t._group == self:
                return t
        return None

    def find_subgroup_things(self, thing_group_type, thing_type):
        subgroups = []
        my_things = set(self.find_member_things(thing_type))
        for g in self._network.all_groups():
            if g == self:
                continue
            group_things = set(g.find_member_things(thing_type))
            thing = g.get_thing(thing_group_type)
            if thing and group_things <= my_things:
                subgroups.append(thing)
        return subgroups
