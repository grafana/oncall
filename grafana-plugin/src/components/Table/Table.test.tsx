import React from 'react';

import { render } from '@testing-library/react';

import Table from './Table';

describe('Table', () => {
  test('it renders pagination related data properly', () => {
    const component = render(
      <Table
        data={[{ foo: 'bar' }, { foo: 'baz' }]}
        columns={[
          {
            title: 'Testy test',
            dataIndex: 'foo',
          },
        ]}
        pagination={{
          next: 'asdfasdf',
          previous: 'mcnmcvmn',
          page_size: 50,
          count: 2,
          current_page_number: 1,
          total_pages: 3,
          onChange: jest.fn(),
        }}
      />
    );
    expect(component.container).toMatchSnapshot();
  });
});
