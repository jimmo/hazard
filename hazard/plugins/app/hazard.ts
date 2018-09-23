export class Thing {
  id: number;
  name: string;
  features: string[];
  zone: string;
  type: string;
  location: Location;

  // Type-specific properties.
  buttons: SwitchButton[];

  static fromJSON(json: any) {
    const thing = new Thing();

    thing.id = json.id;
    thing.name = json.name;
    thing.features = json.features;
    thing.zone = json.zone;
    thing.type = json.type;
    thing.location = Location.fromJSON(json.location);

    thing.buttons = json.buttons ? json.buttons.map(SwitchButton.fromJSON) : [];
    return thing;
  }

  static async load(): Promise<Thing[]> {
    let response = await fetch('/api/rest/thing/list');
    let things = await response.json();
    return things.map(Thing.fromJSON);
  }

  async action(action: string, data?: any): Promise<any> {
    data = data || {};
    let response = await fetch('/api/rest/thing/' + this.id + '/action/' + action, {
      method: 'POST',
      body: JSON.stringify(data),
      headers: new Headers({
        'Content-Type': 'application/json'
      })
    });

    return await response.json();
  }

  hasFeature(feature: string) {
    return this.features.indexOf(feature) >= 0;
  }

  async save() {
    let response = await fetch('/api/rest/thing/' + this.id, {
      method: 'POST',
      body: JSON.stringify(this),
      headers: new Headers({
        'Content-Type': 'application/json'
      })
    });
    return await response.json();
  }
}

export class SwitchButton {
  code: SwitchButtonCode;

  static fromJSON(json: any) {
    const btn = new SwitchButton();
    btn.code = SwitchButtonCode.fromJSON(json.code);
    return btn;
  }
}

export class SwitchButtonCode {
  tap: string;
  doubleTap: string;

  static fromJSON(json: any) {
    const code = new SwitchButtonCode();
    code.tap = json.tap;
    code.doubleTap = json.double_tap;
    return code;
  }
}

export class Location {
  x: number;
  y: number;

  static fromJSON(json: any) {
    const location = new Location();
    location.x = json.x;
    location.y = json.y;
    return location;
  }
}

export class ThingType {
}

//   export async function thingSave(thing: Thing) {
//   }

// export async function loadThingTypes(): Promise<ThingType[]> {
//   // if (loadThingTypes.__cached) {
//   //   return loadThingTypes.__cached;
//   // }
//   let response = await fetch('/api/rest/thing/types');
//   let list = await response.json();
//   // loadThingTypes.__cached = list;
//   return list;
// }

// export function thingHasFeature(thing: Thing, feature: string) {
//   return thing.features.indexOf(feature) >= 0;
// }
