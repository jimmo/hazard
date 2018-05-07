async function loadThings() {
  let response = await fetch('/api/rest/thing/list');
  let things = await response.json();
  return things;
}

async function thingAction(thing, action, data) {
  let response = await fetch('/api/rest/thing/' + thing.id + '/action/' + action, {
    method: 'POST',
    body: JSON.stringify(data),
    headers: new Headers({
      'Content-Type': 'application/json'
    })
  });

  return await response.json();
}

async function thingSave(thing) {
  let response = await fetch('/api/rest/thing/' + thing.id, {
    method: 'POST',
    body: JSON.stringify(thing),
    headers: new Headers({
      'Content-Type': 'application/json'
    })
  });
  return await response.json();
}

async function loadThingTypes() {
  if (loadThingTypes.__cached) {
    return loadThingTypes.__cached;
  }
  let response = await fetch('/api/rest/thing/types');
  let list = await response.json();
  loadThingTypes.__cached = list;
  return list;
}

function sortHelper() {
  const keys = arguments;
  return function(a, b) {
    for (const k of keys) {
      if (a[k] < b[k]) {
        return -1;
      } else if (a[k] > b[k]) {
        return 1;
      }
    }
    return 0;
  }
}

function thingHasFeature(thing, f) {
  return thing.features.indexOf(f) >= 0;
}
