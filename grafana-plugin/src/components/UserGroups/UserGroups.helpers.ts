import { Item } from './UserGroups.types';

export const toPlainArray = (groups: string[][]) => {
  const items: Item[] = [];
  groups.forEach((_group: string[], groupIndex: number) => {
    items.push({
      key: `group-${groupIndex}`,
      type: 'group',
      data: { name: `Recurrence group ${groupIndex + 1}` },
    });

    groups[groupIndex].forEach((item: string, itemIndex: number) => {
      items.push({
        key: `item-${groupIndex}-${itemIndex}`,
        type: 'item',
        data: item,
      });
    });
  });

  return items;
};

export const fromPlainArray = (items: Item[], createNewGroup = false, deleteEmptyGroups = true) => {
  return items
    .reduce((memo: any, item: Item, currentIndex: number) => {
      if (item.type === 'item') {
        let lastGroup = memo[memo.length - 1];
        if (!lastGroup || (createNewGroup && currentIndex === items.length - 1)) {
          lastGroup = [];
          memo.push(lastGroup);
        }
        lastGroup.push(item.data);
      } else {
        memo.push([]);
      }

      return memo;
    }, [])
    .filter((group: string[][]) => !deleteEmptyGroups || group.length);
};
