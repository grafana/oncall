import React from 'react';

import { render } from '@testing-library/react';

import DownloadIcons from './';

describe('DownloadIcons', () => {
  test('it renders properly', () => {
    const component = render(<DownloadIcons />);
    expect(component.container).toMatchSnapshot();
  });
});
