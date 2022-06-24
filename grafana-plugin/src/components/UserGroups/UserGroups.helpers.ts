import { getRandomTimezone } from 'components/UsersTimezones/UsersTimezones.helpers';

export const getRandomGroups = () => {
  return [
    [
      { id: 13, name: 'Maxim Mordasov', tz: 'Europe/Moscow' },
      { id: 2, name: 'Raphael Batyrbaev', tz: 'Europe/Rome' },
    ],
    [
      { id: 5, name: 'Michael Derynck', tz: 'America/Vancouver' },
      { id: 10, name: 'Ildar Iskhakov', tz: 'Asia/Yerevan' },
      { id: 7, name: 'Innokentii Konstantinov', tz: 'Asia/Yerevan' },
    ],
    [
      { id: 5, name: 'Michael Derynck', tz: 'America/Vancouver' },
      { id: 10, name: 'Vadim Stepanov', tz: 'Asia/Yekaterinburg' },
      { id: 7, name: 'Innokentii Konstantinov', tz: 'Asia/Yerevan' },
    ],
  ];
};

export const toPlainArray = (groups) => {
  let i = 0;

  const items = [];
  groups.forEach((group, groupIndex) => {
    items.push({
      index: i++,
      key: `group-${groupIndex}`,
      type: 'group',
      data: { name: `Group ${groupIndex + 1}` },
    });

    groups[groupIndex].forEach((item, itemIndex) => {
      items.push({
        index: i++,
        key: `item-${groupIndex}-${itemIndex}`,
        type: 'item',
        data: item,
      });
    });
  });

  return items;
};

export const fromPlainArray = (items, createNewGroup = false, deleteEmptyGroups = true) => {
  const groups = [];

  return items
    .reduce((memo, item, currentIndex) => {
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
    .filter((group) => !deleteEmptyGroups || group.length);
};
