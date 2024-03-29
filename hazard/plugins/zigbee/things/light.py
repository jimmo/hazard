import logging

from hazard.thing import register_thing
from hazard.things import Light
from hazard.plugins.zigbee.common import ZigBeeTimeout, ZigBeeDeliveryFailure

import zcl.spec

import random

TRANSITION_TIME_HARD = 0
TRANSITION_TIME_SOFT = 2

LOW_LEVEL = 0.1

LOG = logging.getLogger("hazard")


@register_thing
class ZigBeeLight(Light):
    def __init__(self, hazard):
        super().__init__(hazard)
        self._device = None
        self._endpoint = None
        self._groups = []

    async def create_from_device(self, device):
        self._device = device
        self._device.register_zcl(self._on_zcl)
        self._name = device._name

        active_eps = await device.zdo("active_ep", addr16=device._addr16)
        for endpoint in active_eps["active_eps"]:
            desc = await device.zdo(
                "simple_desc", addr16=device._addr16, endpoint=endpoint
            )
            desc = desc["simple_descriptors"][0]
            self._endpoint = desc["endpoint"]
            break

    async def _on_zcl(
        self,
        source_endpoint,
        dest_endpoint,
        cluster_name,
        command_type,
        command_name,
        **kwargs
    ):
        if (
            command_type == zcl.spec.ZclCommandType.PROFILE
            and command_name == "report_attributes"
        ):
            if cluster_name == "onoff":
                self._on = bool(kwargs["attributes"][0]["value"])
                LOG.info('Update "%s" onoff=%s', self._name, self._on)
            elif cluster_name == "level_control":
                self._level = (kwargs["attributes"][0]["value"] - 1) / 253
                LOG.info('Update "%s" level=%f', self._name, self._level)
            elif cluster_name == "color":
                if kwargs["attributes"][0]["attribute"] == 7:
                    mireds = kwargs["attributes"][0]["value"]
                    self._temperature = int(1e6 / mireds)
                    LOG.info(
                        'Update "%s" temperature=%f', self._name, self._temperature
                    )
                elif kwargs["attributes"][0]["attribute"] == 1:
                    self._saturation = kwargs["attributes"][0]["value"] / 255
                    LOG.info('Update "%s" saturation=%f', self._name, self._saturation)
                elif kwargs["attributes"][0]["attribute"] == 0:
                    self._hue = kwargs["attributes"][0]["value"] / 255
                    LOG.info('Update "%s" hue=%f', self._name, self._hue)
            else:
                LOG.error(
                    "unknown light attribute",
                    source_endpoint,
                    dest_endpoint,
                    cluster_name,
                    command_type,
                    command_name,
                    repr(kwargs),
                )

            self.update_groups()

    def update_groups(self):
        for addr16 in self._groups:
            g = self._device._network.find_group(addr16)
            t = g.get_thing(ZigBeeLightGroup)
            if t:
                t.update()

    async def on(self, soft=False):
        if not self._device:
            return
        prev = self._on
        await super().on()
        LOG.info('Sending ON command to "%s"', self._name)
        try:
            if soft:
                await self._device.zcl_cluster(
                    zcl.spec.Profile.HOME_AUTOMATION,
                    self._endpoint,
                    "level_control",
                    "move_to_level_on_off",
                    timeout=5,
                    level=int(self._level * 255),
                    time=TRANSITION_TIME_SOFT,
                )
            else:
                await self._device.zcl_cluster(
                    zcl.spec.Profile.HOME_AUTOMATION,
                    self._endpoint,
                    "onoff",
                    "on",
                    timeout=5,
                )
            LOG.debug(' --> done ("%s")', self._name)
        except (
            ZigBeeDeliveryFailure,
            ZigBeeTimeout,
        ) as e:
            LOG.debug(' --> failed ("%s"): %s', self._name, e)
            self._on = prev
        self.update_groups()

    async def off(self, soft=False):
        if not self._device:
            return
        prev = self._on
        await super().off()
        LOG.info('Sending OFF command to "%s"', self._name)
        try:
            if soft and self._level > LOW_LEVEL:
                await self._device.zcl_cluster(
                    zcl.spec.Profile.HOME_AUTOMATION,
                    self._endpoint,
                    "level_control",
                    "move_to_level_on_off",
                    timeout=5,
                    level=0,
                    time=TRANSITION_TIME_SOFT,
                )
            else:
                await self._device.zcl_cluster(
                    zcl.spec.Profile.HOME_AUTOMATION,
                    self._endpoint,
                    "onoff",
                    "off",
                    timeout=5,
                )
            LOG.debug(' --> done ("%s")', self._name)
        except (
            ZigBeeDeliveryFailure,
            ZigBeeTimeout,
        ) as e:
            LOG.debug(' --> failed ("%s"): %s', self._name, e)
            self._on = prev
        self.update_groups()

    async def toggle(self):
        if not self._device:
            return
        await super().toggle()
        await self._device.zcl_cluster(
            zcl.spec.Profile.HOME_AUTOMATION,
            self._endpoint,
            "onoff",
            "toggle",
            timeout=5,
        )

    async def level(self, level=None, delta=None, onoff=False, soft=False):
        if not self._device:
            return
        prev_on = self._on
        prev_level = self._level
        await super().level(level, delta)
        command = "move_to_level"
        if onoff:
            command += "_on_off"
        time = TRANSITION_TIME_SOFT if soft else TRANSITION_TIME_HARD
        LOG.info('Sending LEVEL command to "%s"', self._name)
        try:
            await self._device.zcl_cluster(
                zcl.spec.Profile.HOME_AUTOMATION,
                self._endpoint,
                "level_control",
                command,
                timeout=5,
                level=int(self._level * 255),
                time=time,
            )
            LOG.debug(' --> done ("%s")', self._name)
        except (
            ZigBeeDeliveryFailure,
            ZigBeeTimeout,
        ):
            LOG.debug(' --> failed ("%s")', self._name)
            self._on = prev_on
            self._level = prev_level
        self.update_groups()

    async def hue(self, hue=None, delta=None):
        if not self._device:
            return
        await super().hue(hue, delta)
        await self._device.zcl_cluster(
            zcl.spec.Profile.HOME_AUTOMATION,
            self._endpoint,
            "color",
            "move_to_hue",
            timeout=5,
            hue=int(self._hue * 253),
            dir=0,
            time=TRANSITION_TIME_SOFT,
        )
        self.update_groups()

    async def saturation(self, saturation):
        if not self._device:
            return
        await super().saturation(saturation)
        await self._device.zcl_cluster(
            zcl.spec.Profile.HOME_AUTOMATION,
            self._endpoint,
            "color",
            "move_to_hue_saturation",
            timeout=5,
            hue=int(self._hue * 253),
            saturation=int(self._saturation * 253),
            dir=0,
            time=TRANSITION_TIME_SOFT,
        )
        self.update_groups()

    async def temperature(self, temperature):
        if not self._device:
            return
        await super().temperature(temperature)
        mireds = int(1e6 / temperature)
        await self._device.zcl_cluster(
            zcl.spec.Profile.HOME_AUTOMATION,
            self._endpoint,
            "color",
            "move_to_color_temperature",
            timeout=5,
            mireds=mireds,
            time=TRANSITION_TIME_SOFT,
        )
        self.update_groups()

    async def disable_reporting(self):
        await self._device.zcl_profile(
            zcl.spec.Profile.HOME_AUTOMATION,
            self._endpoint,
            "level_control",
            "configure_reporting",
            timeout=5,
            configs=[
                {
                    "attribute": 0,
                    "datatype": "uint8",
                    "minimum": 0xFFFF,
                    "maximum": 0x0000,
                    "delta": 10,
                }
            ],
        )
        await self._device.zcl_profile(
            zcl.spec.Profile.HOME_AUTOMATION,
            self._endpoint,
            "onoff",
            "configure_reporting",
            timeout=5,
            configs=[
                {
                    "attribute": 0,
                    "datatype": "bool",
                    "minimum": 0xFFFF,
                    "maximum": 0x0000,
                }
            ],
        )

    async def configure_reporting(self):
        await self._device.zcl_profile(
            zcl.spec.Profile.HOME_AUTOMATION,
            self._endpoint,
            "level_control",
            "configure_reporting",
            timeout=5,
            configs=[
                {
                    "attribute": 0,
                    "datatype": "uint8",
                    "minimum": 5,
                    "maximum": 0,
                    "delta": 10,
                }
            ],
        )
        await self._device.zcl_profile(
            zcl.spec.Profile.HOME_AUTOMATION,
            self._endpoint,
            "onoff",
            "configure_reporting",
            timeout=5,
            configs=[
                {
                    "attribute": 0,
                    "datatype": "bool",
                    "minimum": 5,
                    "maximum": 240 + random.randint(0, 15),
                }
            ],
        )

    async def update_group_membership(self):
        group_ids = [g._addr16 for g in self._device._network.all_groups()]
        memberships = await self._device.zcl_cluster(
            zcl.spec.Profile.HOME_AUTOMATION,
            self._endpoint,
            "groups",
            "get_group_membership",
            ids=group_ids,
        )
        # ('get_group_membership_response', {'capacity': 3, 'ids': [3, 4, 8, 16, 18]})
        self._groups = []
        for addr16 in memberships[1].get("ids", []):
            self._groups.append(addr16)

    async def reconfigure(self):
        await super().reconfigure()
        await self.update_group_membership()
        await self.configure_reporting()

    def to_json(self):
        json = super().to_json()
        json.update(
            {
                "device": self._device.addr64hex() if self._device else None,
                "endpoint": self._endpoint,
                "groups": self._groups,
            }
        )
        return json

    def load_json(self, json):
        super().load_json(json)
        self._device = (
            self._hazard.find_plugin("ZigBeePlugin")
            .network()
            .find_device(json["device"])
        )
        self._device.register_zcl(self._on_zcl)
        self._endpoint = json["endpoint"]
        self._groups = json.get("groups", [])


@register_thing
class ZigBeeLightGroup(Light):
    def __init__(self, hazard):
        super().__init__(hazard)
        self._group = None
        self._endpoint = None

    async def create_from_group(self, group):
        self._group = group
        self._name = group._name

        # TODO: Query endpoints from group devices.
        self._endpoint = 3

    def update(self):
        self._on = self.any_member_on()

    def max_member_level(self):
        return max(
            light._level if light._on else 0
            for light in self._group.find_member_things(ZigBeeLight)
        )

    def any_member_on(self):
        return any(light._on for light in self._group.find_member_things(ZigBeeLight))

    def _member_temperatures(self):
        return [
            light._temperature
            for light in self._group.find_member_things(ZigBeeLight)
            if light._on
        ]

    def min_member_temperature(self):
        t = self._member_temperatures()
        return int(min(t)) if t else None

    def max_member_temperature(self):
        t = self._member_temperatures()
        return int(max(t)) if t else None

    async def on(self, soft=False):
        if not self._group:
            return
        await super().on()
        for light in self._group.find_member_things(ZigBeeLight):
            await super(ZigBeeLight, light).on()
        for light_group in self._group.find_subgroup_things(
            ZigBeeLightGroup, ZigBeeLight
        ):
            await super(ZigBeeLightGroup, light_group).on()

        LOG.info('Sending ON command to group "%s"', self._name)
        if soft:
            await self._group.zcl_cluster(
                zcl.spec.Profile.HOME_AUTOMATION,
                self._endpoint,
                "level_control",
                "move_to_level_on_off",
                timeout=5,
                level=int(self._level * 253) + 1,
                time=TRANSITION_TIME_SOFT,
            )
        else:
            await self._group.zcl_cluster(
                zcl.spec.Profile.HOME_AUTOMATION,
                self._endpoint,
                "onoff",
                "on",
                timeout=5,
            )
        LOG.debug(' --> done ("%s")', self._name)

    async def off(self, soft=False):
        if not self._group:
            return

        # Cache this before we turn off all the members.
        max_member_level = self.max_member_level()

        await super().off()
        for light in self._group.find_member_things(ZigBeeLight):
            await super(ZigBeeLight, light).off()
        for light_group in self._group.find_subgroup_things(
            ZigBeeLightGroup, ZigBeeLight
        ):
            await super(ZigBeeLightGroup, light_group).off()

        LOG.info('Sending OFF command to group "%s"', self._name)
        if soft and max_member_level > LOW_LEVEL:
            await self._group.zcl_cluster(
                zcl.spec.Profile.HOME_AUTOMATION,
                self._endpoint,
                "level_control",
                "move_to_level_on_off",
                timeout=5,
                level=0,
                time=TRANSITION_TIME_SOFT,
            )
        else:
            await self._group.zcl_cluster(
                zcl.spec.Profile.HOME_AUTOMATION,
                self._endpoint,
                "onoff",
                "off",
                timeout=5,
            )
        LOG.debug(' --> done ("%s")', self._name)

    async def toggle(self):
        if not self._group:
            return
        await super().toggle()
        await self._group.zcl_cluster(
            zcl.spec.Profile.HOME_AUTOMATION,
            self._endpoint,
            "onoff",
            "toggle",
            timeout=5,
        )

    async def level(self, level=None, delta=None, onoff=False, soft=False):
        if not self._group:
            return
        await super().level(level, delta)
        for light in self._group.find_member_things(ZigBeeLight):
            await super(ZigBeeLight, light).level(level, delta)
        for light_group in self._group.find_subgroup_things(
            ZigBeeLightGroup, ZigBeeLight
        ):
            await super(ZigBeeLightGroup, light_group).level(level, delta)

        command = "move_to_level"
        if onoff:
            command += "_on_off"
        time = TRANSITION_TIME_SOFT if soft else TRANSITION_TIME_HARD
        await self._group.zcl_cluster(
            zcl.spec.Profile.HOME_AUTOMATION,
            self._endpoint,
            "level_control",
            command,
            timeout=5,
            level=int(self._level * 255),
            time=time,
        )

    async def hue(self, hue):
        if not self._group:
            return
        await super().hue(hue)
        for light in self._group.find_member_things(ZigBeeLight):
            await super(ZigBeeLight, light).hue(hue)
        for light_group in self._group.find_subgroup_things(
            ZigBeeLightGroup, ZigBeeLight
        ):
            await super(ZigBeeLightGroup, light_group).hue(hue)

        await self._group.zcl_cluster(
            zcl.spec.Profile.HOME_AUTOMATION,
            self._endpoint,
            "color",
            "move_to_hue",
            timeout=5,
            hue=int(hue * 253),
            dir=0,
            time=TRANSITION_TIME_SOFT,
        )

    async def saturation(self, saturation):
        if not self._group:
            return
        await super().saturation(saturation)
        for light in self._group.find_member_things(ZigBeeLight):
            await super(ZigBeeLight, light).saturation(saturation)
        for light_group in self._group.find_subgroup_things(
            ZigBeeLightGroup, ZigBeeLight
        ):
            await super(ZigBeeLightGroup, light_group).saturation(saturation)

        await self._group.zcl_cluster(
            zcl.spec.Profile.HOME_AUTOMATION,
            self._endpoint,
            "color",
            "move_to_hue_saturation",
            timeout=5,
            hue=int(hue * 253),
            saturation=int(saturation * 253),
            dir=0,
            time=TRANSITION_TIME_SOFT,
        )

    async def temperature(self, temperature):
        if not self._group:
            return
        await super().temperature(temperature)
        for light in self._group.find_member_things(ZigBeeLight):
            await super(ZigBeeLight, light).temperature(temperature)
        for light_group in self._group.find_subgroup_things(
            ZigBeeLightGroup, ZigBeeLight
        ):
            await super(ZigBeeLightGroup, light_group).temperature(temperature)

        mireds = int(1e6 / temperature)
        await self._group.zcl_cluster(
            zcl.spec.Profile.HOME_AUTOMATION,
            self._endpoint,
            "color",
            "move_to_color_temperature",
            timeout=5,
            mireds=mireds,
            time=TRANSITION_TIME_SOFT,
        )

    async def dim(self, soft=False):
        if not self._group or not self._on:
            return
        if self.max_member_level() > LOW_LEVEL:
            return await self.level(delta=-0.2)

        lights = self._group.find_member_things(ZigBeeLight)
        if sum(t._on for t in lights) == 1:
            return

        random.shuffle(lights)
        lights.sort(key=lambda t: t._priority)
        for light in lights:
            if light._on:
                return await light.off(soft=soft)

    async def undim(self, soft=False):
        if not self._group:
            return

        lights = self._group.find_member_things(ZigBeeLight)
        random.shuffle(lights)
        lights.sort(key=lambda t: -t._priority)
        for light in lights:
            if not light._on:
                return await light.level(level=LOW_LEVEL, onoff=True, soft=soft)

        return await self.level(delta=0.2)

    def to_json(self):
        json = super().to_json()
        json.update(
            {
                "group": self._group._addr16 if self._group else None,
                "endpoint": self._endpoint,
            }
        )
        return json

    def load_json(self, json):
        super().load_json(json)
        self._group = (
            self._hazard.find_plugin("ZigBeePlugin").network().find_group(json["group"])
        )
        self._endpoint = json["endpoint"]

    def _features(self):
        return super()._features() + ["group"]

    async def reconfigure(self):
        await super().reconfigure()
        for light in self._group.find_member_things(ZigBeeLight):
            try:
                await light.reconfigure()
            except:
                pass
