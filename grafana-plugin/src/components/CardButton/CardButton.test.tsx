import 'jest/matchMedia.ts';
import React from 'react';

import { fireEvent, render, screen } from '@testing-library/react';

import CardButton from 'components/CardButton/CardButton';

describe('CardButton', () => {
  function getProps(onClickMock: jest.Mock = jest.fn()) {
    return {
      icon: <></>,
      description: 'Description',
      title: 'Title',
      selected: true,
      onClick: onClickMock,
    };
  }

  test('It updates class and calls onClick prop on click', () => {
    const onClickMock = jest.fn();
    render(<CardButton {...getProps(onClickMock)} />);

    const rootEl = getRootBlockEl();

    fireEvent.click(rootEl);

    expect(rootEl.classList).toContain('root_selected');
    expect(onClickMock).toHaveBeenCalled();
  });

  function getRootBlockEl(): HTMLElement {
    return screen.queryByTestId<HTMLElement>('test__cardButton');
  }
});
