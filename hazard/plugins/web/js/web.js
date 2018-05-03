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
