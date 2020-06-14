export function sortBy(...keys: string[]) {
  return function(a: any, b: any) {
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

export class Serializer {
  static types: Map<string, new () => any> = new Map();

  static register<T>(ctor: new () => T) {
    Serializer.types.set(ctor.name, ctor);
  }

  static serialize(obj: any) {
    return JSON.stringify(obj);
  }

  static create(obj: any) {
    if (obj === null || obj === undefined) {
      return obj;
    }
    if (typeof (obj) === 'object') {
      const typeName = obj['json_type'] || obj['type'];
      if (typeName) {
        let result: any = {};
        const ctor = Serializer.types.get(typeName);
        if (ctor) {
          result = new ctor();
        } else {
          console.log('Unknown serializer type ' + typeName);
        }

        for (const key of Object.keys(obj)) {
          result[key] = Serializer.create(obj[key]);
        }

        return result;
      } else if (obj.length !== undefined) {
        return obj.map(Serializer.create);
      } else {
        return obj;
      }
    } else {
      return obj;
    }
  }

  static deserialize(obj: any) {
    return Serializer.create(obj);
  }
}
