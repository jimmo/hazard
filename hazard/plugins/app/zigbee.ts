import { Surface, Form, Button, Label, CoordAxis, Tree, TreeNode, SimpleTreeNode, ButtonGroup, SimpleTreeLeafNode, Dialog, TextBox, AlertDialog } from 'canvas-forms';

let form: Form = null;

export interface ZigBeeDevice {
  addr64: string;
  addr16: string;
  name: string;
}

export interface ZigBeeEndpoint {
  profile: ZigBeeProfile;
  endpoint: number;
  in_clusters: ZigBeeCluster[];
  out_clusters: ZigBeeCluster[];
}

export interface ZigBeeProfile {
  name: string;
}

export interface ZigBeeCluster {
  name: string;
  cluster: number;
  rx_commands: ZigBeeClusterCommand[];
}

export interface ZigBeeClusterCommand {
  name: string;
  args: string;
};

export interface ZigBeeZdo {
  cluster_name: string;
  args: string;
}

export async function loadDevices(): Promise<ZigBeeDevice[]> {
  let response = await fetch('/api/zigbee/device/list');
  let devices = await response.json();
  return devices;
}

export async function renameDevice(device: ZigBeeDevice, name: string) {
  device.name = name;

  let response = await fetch('/api/zigbee/device/' + device.addr64, {
    method: 'POST',
    body: JSON.stringify(device),
    headers: new Headers({
      'Content-Type': 'application/json'
    })
  });

  return await response.json();
}

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

export async function sendZdo(device: ZigBeeDevice, clusterName: string, data: any) {
  data = data || {};
  let response = await fetch('/api/zigbee/device/' + device.addr64 + '/zdo/' + clusterName, {
    method: 'POST',
    body: JSON.stringify(data),
    headers: new Headers({
      'Content-Type': 'application/json'
    })
  });
  return await response.json();
}

export async function sendZclCluster(device: ZigBeeDevice, endpoint: ZigBeeEndpoint, clusterName: string, commandName: string, data: any) {
  data = data || {};
  let response = await fetch('/api/zigbee/device/' + device.addr64 + '/zcl/cluster/' + endpoint.profile.name + '/' + endpoint.endpoint + '/' + clusterName + '/' + commandName, {
    method: 'POST',
    body: JSON.stringify(data),
    headers: new Headers({
      'Content-Type': 'application/json'
    })
  });
  return await response.json();
}

export async function sendGroupZclCluster(group: number, endpoint: ZigBeeEndpoint, clusterName: string, commandName: string, data: any) {
  data = data || {};
  let response = await fetch('/api/zigbee/group/' + group + '/zcl/cluster/' + endpoint.profile.name + '/' + endpoint.endpoint + '/' + clusterName + '/' + commandName, {
    method: 'POST',
    body: JSON.stringify(data),
    headers: new Headers({
      'Content-Type': 'application/json'
    })
  });
  return await response.json();
}

export async function loadEndpoints(device: ZigBeeDevice) {
  let activeEps = await sendZdo(device, 'active_ep', { 'addr16': device.addr16 });
  let endpoints = [];
  for (let ep of activeEps['active_eps']) {
    let desc = await sendZdo(device, 'simple_desc', { 'addr16': device.addr16, 'endpoint': ep });
    desc = desc['simple_descriptors'][0];
    desc['profile'] = await getProfileById(desc['profile']);
    endpoints.push(desc);
  }
  return endpoints;
}

export async function createThingFromDevice(device: ZigBeeDevice, thingType: string) {
  let response = await fetch('/api/zigbee/device/' + device.addr64 + '/create', {
    method: 'POST',
    body: JSON.stringify({
      'type': thingType,
    }),
    headers: new Headers({
      'Content-Type': 'application/json'
    })
  });
  return await response.json();
}



class ZigBeeExplorer extends SimpleTreeNode {
  constructor() {
    super('ZigBee');
  }

  async treeChildren(): Promise<TreeNode[]> {
    const devices = await loadDevices();
    return devices.map(device => new ZigBeeDeviceNode(device));
  }
}

class ZigBeeDeviceNode extends SimpleTreeNode {
  constructor(private readonly device: ZigBeeDevice) {
    super(device.name);
  }

  async treeChildren(): Promise<TreeNode[]> {
    return [
      new ZigBeeDeviceEndpointsNode(this.device),
      new ZigBeeDeviceZdosNode(this.device),
    ];
  }
}

class ZigBeeDeviceEndpointsNode extends SimpleTreeNode {
  constructor(private readonly device: ZigBeeDevice) {
    super('Endpoints');
  }

  async treeChildren(): Promise<TreeNode[]> {
    const endpoints = await loadEndpoints(this.device);
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
    return this.cluster.rx_commands.map(command => new ZigBeeClusterCommandNode(this.device, this.endpoint, this.cluster, command));
  }
}

class ZigBeeClusterCommandNode extends SimpleTreeLeafNode {
  constructor(private readonly device: ZigBeeDevice, private readonly endpoint: ZigBeeEndpoint, private readonly cluster: ZigBeeCluster, readonly command: ZigBeeClusterCommand) {
    super(command.name);
  }

  treeSelect() {
    new ZigBeeCommandDialog(this.device, this.command.args, async (req: any) => {
      return await sendZclCluster(this.device, this.endpoint, this.cluster.name, this.command.name, req);
    }).modal(form);
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

    let response = await sendZdo(this.device, 'bind', {
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
      resp.setText(JSON.stringify(response, null, ' '));

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
      return await sendZdo(this.device, this.zdo.cluster_name, req);
    }).modal(form);
  }
}


export class ZigBeeTree extends Tree {
  constructor() {
    super();
  }

  added() {
    super.added();
    form = this.form();
    this.addRoot(new ZigBeeExplorer());
  }
}
