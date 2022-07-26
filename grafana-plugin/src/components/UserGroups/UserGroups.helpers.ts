import { Item, ItemData } from './UserGroups.types';

export const toPlainArray = (groups: string[][], getItemData: (item: Item['item']) => ItemData) => {
  let i = 0;

  const items: Item[] = [];
  groups.forEach((group: string[], groupIndex: number) => {
    items.push({
      key: `group-${groupIndex}`,
      type: 'group',
      data: { name: `Group ${groupIndex + 1}` },
    });

    groups[groupIndex].forEach((item: string, itemIndex: number) => {
      items.push({
        key: `item-${groupIndex}-${itemIndex}`,
        type: 'item',
        item,
        data: getItemData(item),
      });
    });
  });

  return items;
};

export const fromPlainArray = (items: Item[], createNewGroup = false, deleteEmptyGroups = true) => {
  const groups = [];

  return items
    .reduce((memo: any, item: Item, currentIndex: number) => {
      if (item.type === 'item') {
        let lastGroup = memo[memo.length - 1];
        if (!lastGroup || (createNewGroup && currentIndex === items.length - 1)) {
          lastGroup = [];
          memo.push(lastGroup);
        }
        lastGroup.push(item.item);
      } else {
        memo.push([]);
      }

      return memo;
    }, [])
    .filter((group: string[][]) => !deleteEmptyGroups || group.length);
};
