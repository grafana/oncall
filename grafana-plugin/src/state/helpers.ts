import { Alert } from 'models/alertgroup/alertgroup.types';

type Anims = { [key: number]: number[] };

export function getAnims(oldStats: any, newStats: any, ids: number[]) {
  const anims: Anims = {};

  const map = ids.reduce((acc: any, id: number) => {
    const { list } = newStats[id] || { list: [] };

    list.forEach((alertId: Alert['pk']) => {
      acc[alertId] = { to: id };
    });

    return acc;
  }, {});

  const filteredStats = ids.reduce((acc: any, id: any) => {
    return {
      ...acc,
      [id]: oldStats[id] || { list: [] },
    };
  }, {});

  Object.keys(map)
    .map(Number)
    .forEach((alertId: number) => {
      const id = Object.keys(filteredStats)
        .map(Number)
        .find((id: number) => filteredStats[id].list.includes(alertId));

      const to = map[alertId].to;

      const startIndex = id ? ids.indexOf(id) : -1;
      const endIndex = ids.indexOf(to);

      anims[alertId] = [];
      for (let i = startIndex + 1; i <= endIndex; i++) {
        anims[alertId].push(ids[i]);
      }
    });

  return anims;
}

export function move(arr: any[], old_index: number, new_index: number) {
  while (old_index < 0) {
    old_index += arr.length;
  }
  while (new_index < 0) {
    new_index += arr.length;
  }
  if (new_index >= arr.length) {
    let k = new_index - arr.length;
    while (k-- + 1) {
      arr.push(undefined);
    }
  }
  arr.splice(new_index, 0, arr.splice(old_index, 1)[0]);
  return arr;
}
