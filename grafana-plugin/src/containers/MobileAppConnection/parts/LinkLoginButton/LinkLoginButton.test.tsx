import React from 'react';

import { render } from '@testing-library/react';

import { LinkLoginButton } from './LinkLoginButton';

describe('LinkLoginButton', () => {
  test('it renders properly', () => {
    const component = render(<LinkLoginButton baseUrl="http://test.url" token="test1213" />);
    expect(component.container).toMatchSnapshot();
  });
});
