import 'jest/matchMedia.ts';
import { describe, expect, test } from '@jest/globals';
import { render } from '@testing-library/react';

import React from 'react';

import '@testing-library/jest-dom';
import CardButton from 'components/CardButton/CardButton';

describe('CardButton', () => {
  function getProps() {
    return {
      icon: <></>,
      description: 'Description',
      title: 'Title',
      selected: true,
      onClick: jest.fn(),
    };
  }

  test('Renders', () => {
    render(<CardButton {...getProps()} />);
  });
});
