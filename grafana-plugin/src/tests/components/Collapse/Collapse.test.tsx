import { describe, expect, test } from '@jest/globals';
import { render, fireEvent, screen } from '@testing-library/react';
import { Icon } from '@grafana/ui';

import Collapse, { CollapseProps } from 'components/Collapse/Collapse';
import React from 'react';

import '@testing-library/jest-dom';

describe('Collapse', () => {
  function getProps(isOpen: boolean, onClick: jest.Mock = null) {
    return {
      label: 'Toggle',
      isOpen: false,
      onClick: onClick
    }
  }

  test('It renders the content of children on click', () => {
    const mock = jest.fn()

    render(<Collapse {...getProps(false)} />);

    const hiddenChildrenContent = getChildrenEl();
    expect(hiddenChildrenContent).toBeNull();

    const toggler = getTogglerEl();
    fireEvent.click(toggler);

    expect(mock).toHaveBeenCalledTimes(1);

    expect(hiddenChildrenContent).toBeDefined();
  });

  test('It renders open if isOpen=true', () => {
    render(<Collapse {...getProps(true)} />);

    const content = getChildrenEl();
    expect(content).toBeDefined();
  });

  function getChildrenEl(): HTMLElement {
    return screen.queryByTestId<HTMLElement>('test__children');
  }

  function getTogglerEl(): HTMLElement {
    return screen.getByTestId<HTMLElement>('test__toggle');
  }
});
