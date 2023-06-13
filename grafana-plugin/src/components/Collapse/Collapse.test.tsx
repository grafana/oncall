import 'jest/matchMedia.ts';
import React from 'react';

import { render, fireEvent, screen } from '@testing-library/react';

import Collapse, { CollapseProps } from 'components/Collapse/Collapse';

describe.skip('Collapse', () => {
  function getProps(isOpen: boolean, onClick: jest.Mock = jest.fn()) {
    return {
      label: 'Toggle',
      isOpen: isOpen,
      onClick: onClick,
    } as CollapseProps;
  }

  test('Content becomes visible on click', () => {
    render(<Collapse {...getProps(false)} />);

    const hiddenChildrenContent = getChildrenEl();
    expect(hiddenChildrenContent).toBeNull();

    const toggler = getTogglerEl();
    fireEvent.click(toggler);

    expect(hiddenChildrenContent).toBeDefined();
  });

  test('Content is collapsed for [isOpen=false]', () => {
    render(<Collapse {...getProps(false)} />);

    const content = getChildrenEl();
    expect(content).toBeNull();
  });

  test('Content is not collapsed for [isOpen=true]', () => {
    render(<Collapse {...getProps(true)} />);

    const content = getChildrenEl();
    expect(content).toBeDefined();
  });

  function getChildrenEl(): HTMLElement {
    return screen.queryByTestId<HTMLElement>('test__children');
  }

  function getTogglerEl(): HTMLElement {
    return screen.queryByTestId<HTMLElement>('test__toggle');
  }
});
