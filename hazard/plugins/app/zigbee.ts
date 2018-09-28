import { Surface, Form, Button, Label, CoordAxis, Tree, TreeNode, SimpleTreeNode, ButtonGroup, SimpleTreeLeafNode, Dialog, TextBox, AlertDialog, Ionicons, MenuItems, PromptDialog, MenuItem, MenuSeparatorItem, StaticTree, ConfirmDialog, MenuHeadingItem } from 'canvas-forms';
import { Serializer, sortBy } from './utils';

let form: Form = null;

export class ZigBeeDevice {
  addr64: string;
  addr16: number;
  name: string;

  static async load(): Promise<ZigBeeDevice[]> {
    let response = await fetch('/api/zigbee/device/list');
    return Serializer.deserialize(await response.json());
  }

  async rename(name: string) {
    this.name = name;

    let response = await fetch('/api/zigbee/device/' + this.addr64, {
      method: 'POST',
      body: Serializer.serialize(this),
      headers: new Headers({
        'Content-Type': 'application/json'
      })
    });

    return await response.json();
  }

  async sendZdo(clusterName: string, data: any) {
    data = data || {};
    let response = await fetch('/api/zigbee/device/' + this.addr64 + '/zdo/' + clusterName, {
      method: 'POST',
      body: Serializer.serialize(data),
      headers: new Headers({
        'Content-Type': 'application/json'
      })
    });
    return await response.json();
  }

  async sendZclCluster(endpoint: ZigBeeEndpoint, clusterName: string, commandName: string, data: any) {
    data = data || {};
    let response = await fetch('/api/zigbee/device/' + this.addr64 + '/zcl/cluster/' + endpoint.profile.name + '/' + endpoint.endpoint + '/' + clusterName + '/' + commandName, {
      method: 'POST',
      body: Serializer.serialize(data),
      headers: new Headers({
        'Content-Type': 'application/json'
      })
    });
    return await response.json();
  }

  async sendZclProfile(endpoint: ZigBeeEndpoint, clusterName: string, commandName: string, data: any) {
    data = data || {};
    let response = await fetch('/api/zigbee/device/' + this.addr64 + '/zcl/profile/' + endpoint.profile.name + '/' + endpoint.endpoint + '/' + clusterName + '/' + commandName, {
      method: 'POST',
      body: Serializer.serialize(data),
      headers: new Headers({
        'Content-Type': 'application/json'
      })
    });
    return await response.json();
  }

  async loadEndpoints() {
    let activeEps = await this.sendZdo('active_ep', { 'addr16': this.addr16 });
    let endpoints = [];
    for (let ep of activeEps['active_eps']) {
      let desc = await this.sendZdo('simple_desc', { 'addr16': this.addr16, 'endpoint': ep });
      desc = desc['simple_descriptors'][0];
      desc['profile'] = await getProfileById(desc['profile']);
      endpoints.push(desc);
    }
    return endpoints;
  }

  async createThing(thingType: string) {
    let response = await fetch('/api/zigbee/device/' + this.addr64 + '/thing', {
      method: 'POST',
      body: Serializer.serialize({
        'type': thingType,
      }),
      headers: new Headers({
        'Content-Type': 'application/json'
      })
    });
    return await response.json();
  }
}
Serializer.register(ZigBeeDevice);

export class ZigBeeGroup {
  addr16: number;
  name: string;

  static async load(): Promise<ZigBeeGroup[]> {
    let response = await fetch('/api/zigbee/group/list');
    return Serializer.deserialize(await response.json());
  }

  async rename(name: string) {
    this.name = name;

    let response = await fetch('/api/zigbee/group/' + this.addr16, {
      method: 'POST',
      body: Serializer.serialize(this),
      headers: new Headers({
        'Content-Type': 'application/json'
      })
    });

    return await response.json();
  }

  async remove() {
    let response = await fetch('/api/zigbee/group/' + this.addr16 + '/remove', {
      method: 'POST',
      body: Serializer.serialize({
      }),
      headers: new Headers({
        'Content-Type': 'application/json'
      })
    });

    return await response.json();
  }


  async sendZclCluster(endpoint: ZigBeeEndpoint, clusterName: string, commandName: string, data: any) {
    data = data || {};
    let response = await fetch('/api/zigbee/group/' + this.addr16 + '/zcl/cluster/' + endpoint.profile.name + '/' + endpoint.endpoint + '/' + clusterName + '/' + commandName, {
      method: 'POST',
      body: Serializer.serialize(data),
      headers: new Headers({
        'Content-Type': 'application/json'
      })
    });
    return await response.json();
  }

  static async create() {
    let response = await fetch('/api/zigbee/group/create', {
      method: 'POST',
      body: Serializer.serialize({
      }),
      headers: new Headers({
        'Content-Type': 'application/json'
      })
    });
    return await response.json();
  }

  async createThing(thingType: string) {
    let response = await fetch('/api/zigbee/group/' + this.addr16 + '/thing', {
      method: 'POST',
      body: Serializer.serialize({
        'type': thingType,
      }),
      headers: new Headers({
        'Content-Type': 'application/json'
      })
    });
    return await response.json();
  }


}
Serializer.register(ZigBeeGroup);

export class ZigBeeEndpoint {
  profile: ZigBeeProfile;
  endpoint: number;
  in_clusters: ZigBeeCluster[];
  out_clusters: ZigBeeCluster[];
}
Serializer.register(ZigBeeEndpoint);

export class ZigBeeProfile {
  name: string;
}
Serializer.register(ZigBeeProfile);

export class ZigBeeCluster {
  name: string;
  cluster: number;
  rx_commands: ZigBeeClusterCommand[];
  attributes: ZigBeeClusterAttribute[];
}
Serializer.register(ZigBeeCluster);

export class ZigBeeClusterCommand {
  name: string;
  command: number;
  args: string;
};
Serializer.register(ZigBeeClusterCommand);

export class ZigBeeClusterAttribute {
  name: string;
  attribute: number;
  datatype: string;
};
Serializer.register(ZigBeeClusterAttribute);

export class ZigBeeZdo {
  cluster_name: string;
  args: string;
}
Serializer.register(ZigBeeZdo);

export async function loadStatus() {
  let response = await fetch('/api/zigbee/status');
  let status = await response.json();
  return status;
}

export async function loadSpec() {
  // if (loadSpec.__cached) {
  //   return loadSpec.__cached;
  // }
  let response = await fetch('/api/zigbee/spec');
  let spec = await response.json();
  // loadSpec.__cached = spec;
  return spec;
}

export async function getProfileById(profileId: number) {
  let spec = await loadSpec();
  for (const p of spec['profile']) {
    if (p['profile'] === profileId) {
      return p;
    }
  }
  return null;
}



class ZigBeeExplorer extends StaticTree {
  constructor() {
    super('ZigBee', Ionicons.Hammer);
    this.add(new ZigBeeExplorerDevices());
    this.add(new ZigBeeExplorerGroups());
  }
}

class ZigBeeExplorerDevices extends SimpleTreeNode {
  constructor() {
    super('Devices');
  }

  async treeChildren(): Promise<TreeNode[]> {
    const devices = await ZigBeeDevice.load();
    devices.sort(sortBy('name'));
    return devices.map(device => new ZigBeeDeviceNode(device));
  }
}

class ZigBeeExplorerGroups extends SimpleTreeNode {
  constructor() {
    super('Groups');
  }

  async treeChildren(): Promise<TreeNode[]> {
    const groups = await ZigBeeGroup.load();
    return groups.map(group => new ZigBeeGroupNode(group));
  }

  async treeMenu(): Promise<MenuItems> {
    const create = new MenuItem('New group...');
    create.click.add(async () => {
      ZigBeeGroup.create();
    });

    return [
      create,
    ];
  }
}

class ZigBeeDeviceNode extends SimpleTreeNode {
  constructor(private readonly device: ZigBeeDevice) {
    super(device.name);
  }

  treeText() {
    return this.device.name;
  }

  async treeChildren(): Promise<TreeNode[]> {
    return [
      new ZigBeeDeviceEndpointsNode(this.device),
      new ZigBeeDeviceZdosNode(this.device),
    ];
  }

  async treeMenu(): Promise<MenuItems> {
    const rename = new MenuItem('Rename');
    rename.click.add(async () => {
      const result = await new PromptDialog('Rename ZigBee device', this.device.name).modal(form);
      if (result) {
        this.device.name = result;
        form.repaint();
        this.device.rename(result);
      }
    });

    const items = [
      rename,
      new MenuSeparatorItem(),
    ];

    const createLight = new MenuItem('Create as Light');
    createLight.click.add(async () => {
      this.device.createThing('ZigBeeLight');
    });
    items.push(createLight);

    const createSwitch = new MenuItem('Create as Switch');
    createSwitch.click.add(async () => {
      this.device.createThing('ZigBeeSwitch');
    });
    items.push(createSwitch);

    return items;
  }
}

class ZigBeeDeviceEndpointsNode extends SimpleTreeNode {
  constructor(private readonly device: ZigBeeDevice) {
    super('Endpoints');
  }

  async treeChildren(): Promise<TreeNode[]> {
    const endpoints = await this.device.loadEndpoints();
    return endpoints.map(endpoint => new ZigBeeEndpointNode(this.device, endpoint));
  }
}

class ZigBeeEndpointNode extends SimpleTreeNode {
  constructor(private readonly device: ZigBeeDevice, private readonly endpoint: ZigBeeEndpoint) {
    super(endpoint.endpoint + ' ' + endpoint.profile.name);
  }

  async treeChildren(): Promise<TreeNode[]> {
    return [
      new ZigBeeEndpointClustersNode(this.device, this.endpoint),
      new ZigBeeEndpointBindNode(this.device, this.endpoint),
    ];
  }

  async treeMenu(): Promise<MenuItems> {
    const items: MenuItems = [
      new MenuHeadingItem('Add to group'),
    ];

    const groups = await ZigBeeGroup.load();
    for (const group of groups) {
      const item = new MenuItem(group.name);
      item.click.add(async () => {
        await this.device.sendZclCluster(this.endpoint, 'groups', 'add_group', { 'id': group.addr16, 'name': group.name });
      });
      items.push(item);
    }

    return items;
  }
}

class ZigBeeEndpointClustersNode extends SimpleTreeNode {
  constructor(private readonly device: ZigBeeDevice, private readonly endpoint: ZigBeeEndpoint) {
    super('Clusters');
  }

  async treeChildren(): Promise<TreeNode[]> {
    const spec = await loadSpec();
    let clusters = [];
    for (const cluster of spec['cluster']) {
      if (this.endpoint.in_clusters.indexOf(cluster.cluster) >= 0) {
        clusters.push(cluster);
      }
    }
    return clusters.map(cluster => new ZigBeeInClusterNode(this.device, this.endpoint, cluster));
  }
}

class ZigBeeInClusterNode extends SimpleTreeNode {
  constructor(private readonly device: ZigBeeDevice, private readonly endpoint: ZigBeeEndpoint, private readonly cluster: ZigBeeCluster) {
    super(cluster.name);
  }

  async treeChildren(): Promise<TreeNode[]> {
    return [
      ...this.cluster.rx_commands.map(command => new ZigBeeClusterCommandNode(this.device, this.endpoint, this.cluster, command)),
      ...this.cluster.attributes.map(attribute => new ZigBeeClusterAttributeNode(this.device, this.endpoint, this.cluster, attribute)),
    ];
  }
}

class ZigBeeClusterCommandNode extends SimpleTreeLeafNode {
  constructor(private readonly device: ZigBeeDevice, private readonly endpoint: ZigBeeEndpoint, private readonly cluster: ZigBeeCluster, readonly command: ZigBeeClusterCommand) {
    super(command.name);
  }

  treeSelect() {
    new ZigBeeCommandDialog(this.device, this.command.args, async (req: any) => {
      return await this.device.sendZclCluster(this.endpoint, this.cluster.name, this.command.name, req);
    }).modal(form);
  }
}

class ZigBeeClusterAttributeNode extends SimpleTreeLeafNode {
  constructor(private readonly device: ZigBeeDevice, private readonly endpoint: ZigBeeEndpoint, private readonly cluster: ZigBeeCluster, readonly attribute: ZigBeeClusterAttribute) {
    super('Attribute: ' + attribute.name);
  }

  async treeSelect() {
    const attrs = await this.device.sendZclProfile(this.endpoint, this.cluster.name, 'read_attributes', {
      'attributes': [this.attribute.attribute],
    });
    console.log(attrs[1].attributes[0].value);
  }
}

class ZigBeeEndpointBindNode extends SimpleTreeNode {
  constructor(private readonly device: ZigBeeDevice, private readonly endpoint: ZigBeeEndpoint) {
    super('Bind');
  }

  async treeChildren(): Promise<TreeNode[]> {
    const spec = await loadSpec();
    let clusters = [];
    for (const cluster of spec['cluster']) {
      if (this.endpoint.out_clusters.indexOf(cluster.cluster) >= 0) {
        clusters.push(cluster);
      }
    }
    return clusters.map(cluster => new ZigBeeBindClusterNode(this.device, this.endpoint, cluster));
  }
}


class ZigBeeBindClusterNode extends SimpleTreeLeafNode {
  constructor(private readonly device: ZigBeeDevice, private readonly endpoint: ZigBeeEndpoint, private readonly cluster: ZigBeeCluster) {
    super(cluster.name);
  }

  async treeSelect() {
    const status = await loadStatus();

    let response = await this.device.sendZdo('bind', {
      'src_addr': this.device.addr64,
      'src_ep': this.endpoint.endpoint,
      'cluster': this.cluster.cluster,
      'dst_addr_mode': 3,  // 64-bit device.
      'dst_addr': status['coordinator_addr64'],
      'dst_ep': 1,
    });

    new AlertDialog(JSON.stringify(response, null, '  ')).modal(form);
  }
}

class ZigBeeCommandDialog extends Dialog {
  constructor(private readonly device: ZigBeeDevice, private readonly args: string, private readonly callback: (req: any) => Promise<any>) {
    super();

    const obj: any = {};
    for (const arg_ of this.args) {
      const arg = arg_.split(':');
      obj[arg[0]] = arg[1];
      if (arg[0] === 'addr16') {
        obj[arg[0]] = this.device.addr16;
      }
      if (arg[0] === 'addr64') {
        obj[arg[0]] = this.device.addr64;
      }
    }

    this.add(new Label('Request JSON'), 10, 10, 200);
    const req = this.add(new TextBox(JSON.stringify(obj, null, '  ')), { x: 10, y: 38, x2: 10, h: 200 });
    req.multiline = true;

    const send = this.add(new Button('Send'), { w: 100, x2: 10, y: 250 });


    this.add(new Label('Response JSON'), 10, 290, 200);
    const resp = this.add(new TextBox(), { x: 10, y: 318, x2: 10, h: 200 });
    resp.multiline = true;

    const close = this.add(new Button('Close'), { w: 100, x2: 10, y2: 10 });


    send.click.add(async () => {
      const response = await this.callback(JSON.parse(req.text));
      resp.text = JSON.stringify(response, null, ' ');

    });

    close.click.add(() => {
      this.close();
    });
  }

  defaultConstraints() {
    this.coords.size(420, 580);
    super.defaultConstraints();
  }
}


class ZigBeeDeviceZdosNode extends SimpleTreeNode {
  constructor(private readonly device: ZigBeeDevice) {
    super('ZDO');
  }

  async treeChildren(): Promise<TreeNode[]> {
    const spec = await loadSpec();
    return spec['zdo'].map((zdo: any) => new ZigBeeDeviceZdoNode(this.device, zdo));
  }
}

class ZigBeeDeviceZdoNode extends SimpleTreeLeafNode {
  constructor(private readonly device: ZigBeeDevice, private readonly zdo: ZigBeeZdo) {
    super(zdo.cluster_name);
  }

  treeSelect() {
    new ZigBeeCommandDialog(this.device, this.zdo.args, async (req: any) => {
      return await this.device.sendZdo(this.zdo.cluster_name, req);
    }).modal(form);
  }
}

class ZigBeeGroupNode extends SimpleTreeNode {
  constructor(private readonly group: ZigBeeGroup) {
    super(group.name + ' / ' + group.addr16);
  }

  treeText() {
    return this.group.name + ' / ' + this.group.addr16;
  }

  treeHasChildren() {
    return false;
  }

  async treeMenu(): Promise<MenuItems> {
    const rename = new MenuItem('Rename');
    rename.click.add(async () => {
      const result = await new PromptDialog('Rename ZigBee group', this.group.name).modal(form);
      if (result) {
        this.group.name = result;
        form.repaint();
        this.group.rename(result);
      }
    });

    const remove = new MenuItem('Delete');
    remove.click.add(async () => {
      const result = await new ConfirmDialog('Delete ZigBee group?').modal(form);
      if (result) {
        this.group.remove();
      }
    });

    const items = [
      rename,
      remove,
      new MenuSeparatorItem(),
    ];

    const create = new MenuItem('Create Light Group');
    create.click.add(async () => {
      this.group.createThing('ZigBeeLightGroup');
    });
    items.push(create);

    return items;
  }
}


export class ZigBeeTree extends Tree {
  constructor() {
    super();
  }

  added() {
    super.added();
    form = this.form;
    const root = this.addRoot(new ZigBeeExplorer());
    root.open();
  }
}
