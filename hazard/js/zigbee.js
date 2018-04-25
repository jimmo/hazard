async function loadDevices() {
  let response = await fetch('/api/zigbee/devices');
  let devices = await response.json();
  return devices;
}

async function loadStatus() {
  let response = await fetch('/api/zigbee/status');
  let status = await response.json();
  return status;
}

async function loadSpec() {
  if (loadSpec.__cached) {
    return loadSpec.__cached;
  }
  let response = await fetch('/api/zigbee/spec');
  let spec = await response.json();
  loadSpec.__cached = spec;
  return spec;
}

async function getProfileById(profileId) {
  let spec = await loadSpec();
  for (const p of spec['profile']) {
    if (p['profile'] === profileId) {
      return p;
    }
  }
  return null;
}

async function sendZdo(device, clusterName, data) {
  data = data || {};
  let response = await fetch('/api/zigbee/zdo/' + device.addr64 + '/' + clusterName, {
    method: 'POST',
    body: JSON.stringify(data),
    headers: new Headers({
      'Content-Type': 'application/json'
    })
  });
  return await response.json();
}

async function sendZclCluster(device, endpoint, clusterName, commandName, data) {
  data = data || {};
  let response = await fetch('/api/zigbee/zcl/cluster/' + device.addr64 + '/' + endpoint.profile.name + '/' + endpoint.endpoint + '/' + clusterName + '/' + commandName, {
    method: 'POST',
    body: JSON.stringify(data),
    headers: new Headers({
      'Content-Type': 'application/json'
    })
  });
  return await response.json();
}

async function loadEndpoints(device) {
  let activeEps = await sendZdo(device, 'active_ep', {'addr16': device.addr16});
  let endpoints = [];
  for (let ep of activeEps['active_eps']) {
    let desc = await sendZdo(device, 'simple_desc', { 'addr16': device.addr16, 'endpoint': ep });
    desc = desc['simple_descriptors'][0];
    desc['profile'] = await getProfileById(desc['profile']);
    endpoints.push(desc);
  }
  return endpoints;
}
