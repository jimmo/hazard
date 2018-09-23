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

