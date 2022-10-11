import React, { FC, useState, useCallback, useMemo, ChangeEvent } from 'react';

import { Pagination, Checkbox, Icon, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import Table from 'rc-table';
import { TableProps } from 'rc-table/lib/Table';

import { ExpandIcon } from 'icons';

import styles from './Table.module.css';

const cx = cn.bind(styles);

export interface Props<RecordType = unknown> extends TableProps<RecordType> {
  loading?: boolean;
  pagination?: {
    page: number;
    total: number;
    onChange: (page: number) => void;
  };
  rowSelection?: {
    selectedRowKeys: string[];
    onChange: (selectedRowKeys: string[]) => void;
  };
  expandable?: {
    expandedRowKeys: string[];
    expandedRowRender: (item: any) => React.ReactNode;
    onExpandedRowsChange?: (rows: string[]) => void;
    expandRowByClick: boolean;
    expandIcon?: (props: { expanded: boolean; record: any }) => React.ReactNode;
    onExpand?: (expanded: boolean, item: any) => void;
  };
}

const GTable: FC<Props> = (props) => {
  const { columns, data, className, pagination, loading, rowKey, expandable, ...restProps } = props;

  const { page, total: numberOfPages, onChange: onNavigate } = pagination || {};

  if (expandable) {
    expandable.expandIcon = ({ expanded, record }) => {
      return (
        <div className={cx('expand-icon', { [`expand-icon__expanded`]: expanded })}>
          <ExpandIcon />
        </div>
      );
    };
  }

  return (
    <VerticalGroup justify="flex-end">
      <Table
        rowKey={rowKey}
        className={cx('root', 'filter-table', className)}
        columns={columns}
        data={data}
        expandable={expandable}
        {...restProps}
      />
      {pagination && (
        <div className={cx('pagination')}>
          <Pagination hideWhenSinglePage currentPage={page} numberOfPages={numberOfPages} onNavigate={onNavigate} />
        </div>
      )}
    </VerticalGroup>
  );
};

export default GTable;
