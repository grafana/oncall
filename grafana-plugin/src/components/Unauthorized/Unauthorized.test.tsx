import React from 'react';

import renderer from 'react-test-renderer';

import Unauthorized from 'components/Unauthorized';

import '@testing-library/jest-dom';

describe('Unauthorized', () => {
  test('renders properly', async () => {
    const tree = renderer.create(<Unauthorized />).toJSON();
    expect(tree).toMatchSnapshot();
  });
});
