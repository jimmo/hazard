import { Serializer } from './utils';

class ThingBase {
    id: number;
    name: string;
    zone: string;
    location: ThingLocation;
    features: string[];
}

export class Status {
    title_left: Thing;
    title_center: string;
    title_right: Thing;

    static async load(): Promise<Status> {
        let response = await fetch('/api/rest/status');
        let status = await response.json();
        return Serializer.deserialize(status);
    }
}
Serializer.register(Status);

export class Thing extends ThingBase {
    static async load(): Promise<Thing[]> {
        let response = await fetch('/api/rest/thing/list');
        let things = await response.json();
        return Serializer.deserialize(things);
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

        return Serializer.deserialize(await response.json);
    }

    async reconfigure(): Promise<any> {
        return await this.action('reconfigure');
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
        return Serializer.deserialize(await response.json);
    }

    async remove() {
        let response = await fetch('/api/rest/thing/' + this.id + '/remove', {
            method: 'POST',
            body: JSON.stringify(this),
            headers: new Headers({
                'Content-Type': 'application/json'
            })
        });
        return Serializer.deserialize(await response.json);
    }

    get summary() : string {
        return this.name;
    }
}
Serializer.register(Thing);

export class Action {
    id: number;
    name: string;
    code: string;

    static async load(): Promise<Action[]> {
        let response = await fetch('/api/rest/action/list');
        let actions = await response.json();
        return Serializer.deserialize(actions);
    }

    static async create(): Promise<Action> {
        let response = await fetch('/api/rest/action/create', {
            method: 'POST',
            body: JSON.stringify({}),
            headers: new Headers({
                'Content-Type': 'application/json'
            })
        });
        return Serializer.deserialize(await response.json());
    }

    async invoke(data?: any): Promise<any> {
        data = data || {};
        let response = await fetch('/api/rest/action/' + this.id + '/invoke', {
            method: 'POST',
            body: JSON.stringify(data),
            headers: new Headers({
                'Content-Type': 'application/json'
            })
        });
        return Serializer.deserialize(await response.json());
    }

    async save() {
        let response = await fetch('/api/rest/action/' + this.id, {
            method: 'POST',
            body: JSON.stringify(this),
            headers: new Headers({
                'Content-Type': 'application/json'
            })
        });
        return Serializer.deserialize(await response.json());
    }

    async remove() {
        let response = await fetch('/api/rest/action/' + this.id + '/remove', {
            method: 'POST',
            body: JSON.stringify(this),
            headers: new Headers({
                'Content-Type': 'application/json'
            })
        });
        return Serializer.deserialize(await response.json());
    }
}
Serializer.register(Action);

export class Light extends Thing {
    on: boolean;
    level: number;
    hue: number;
    temperature: number;
    saturation: number;
}
Serializer.register(Light);

export class Switch extends Thing {
    buttons: SwitchButton[];
}
Serializer.register(Switch);

export class SwitchButton {
    code: string;
    name: string;
    tap: string;
    single: string;
    double: string;
}
Serializer.register(SwitchButton);

export class MultiSensor extends Thing {
}
Serializer.register(MultiSensor);

export class Clock extends Thing {
    interval: number;
    code: string;
}
Serializer.register(Clock);

export class ThingLocation {
    x: number;
    y: number;
}
Serializer.register(ThingLocation);

export class Temperature extends Thing {
    temperature: number;
    humidity: number;
    last_update: number;

    protected static plural(n: number, t: string) {
        if (n === 1) {
            return n.toFixed(0) + ' ' + t;
        } else {
            return n.toFixed(0) + ' ' + t + 's';
        }
    }

    protected get age() : number {
        const now = Math.ceil(new Date().getTime() / 1000);
        return Math.max(1, now - this.last_update);
    }

    get displayLastUpdated() : string {
        if (this.last_update === null) {
            return 'Unknown'
        }
        let dt = this.age;
        if (dt < 60) {
            return Temperature.plural(dt, 'second') + ' ago';
        }
        dt /= 60;
        if (dt < 60) {
            return Temperature.plural(dt, 'minute') + ' ago';
        }
        dt /= 60;
        if (dt < 24) {
            return Temperature.plural(dt, 'hour') + ' ago';
        }
        dt /= 24;
        return Temperature.plural(dt, 'day') + ' ago';
    }

    get isRecent() : boolean {
        return this.age < 15 * 60;
    }

    get displayTemperature() : string {
        if (this.temperature === null) {
            return '?';
        } else {
            return this.temperature.toFixed(1) + ' \u2103'
        }
    }
    get displayHumidity() : string {
        if (this.humidity === null) {
            return '?';
        } else {
            return this.humidity.toFixed(1) + ' % rH'
        }
    }

    get summary() : string {
        return this.displayTemperature;
    }
}
Serializer.register(Temperature);

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
