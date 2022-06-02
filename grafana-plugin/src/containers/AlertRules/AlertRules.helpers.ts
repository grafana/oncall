import { toArray } from 'react-emoji-render';

export const parseEmojis = (value: any) => {
  const emojisArray = toArray(value);

  // toArray outputs React elements for emojis and strings for other
  const newValue = emojisArray.reduce((previous, current) => {
    if (typeof current === 'string') {
      return previous + current;
    }
    //@ts-ignore
    return previous + current.props.children;
  }, '');

  return newValue;
};
