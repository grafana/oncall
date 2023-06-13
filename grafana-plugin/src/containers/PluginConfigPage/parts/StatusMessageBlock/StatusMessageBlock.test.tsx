import React from 'react';

import { render } from '@testing-library/react';

import StatusMessageBlock from '.';

describe('StatusMessageBlock', () => {
  test('It renders properly', async () => {
    const component = render(<StatusMessageBlock text="helloooo" />);
    expect(component.baseElement).toMatchSnapshot();
  });
});
