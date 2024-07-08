import React, { FC, useMemo } from 'react';

import { cx } from '@emotion/css';
import { Pagination, VerticalGroup, useStyles2 } from '@grafana/ui';
import Table from 'rc-table';
import { TableProps } from 'rc-table/lib/Table';
import { bem } from 'styles/utils.styles';

import { ExpandIcon } from 'icons/Icons';

import { getTableStyles } from './Table.styles';

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

export const GTable: FC<Props> = (props) => {
  const { columns, data, className, pagination, loading, rowKey, expandable, ...restProps } = props;
  const { page, total: numberOfPages, onChange: onNavigate } = pagination || {};

  const styles = useStyles2(getTableStyles);

  const expandableFn = useMemo(() => {
    return expandable
      ? {
          ...expandable,
          expandIcon: ({ expanded }) => {
            return (
              <div className={cx(styles.expandIcon, { [bem(styles.expandIcon, 'expanded')]: expanded })}>
                <ExpandIcon />
              </div>
            );
          },
          expandedRowClassName: (_record, index) => (index % 2 === 0 ? styles.rowEven : ''),
        }
      : null;
  }, [expandable]);

  return (
    <VerticalGroup justify="flex-end">
      <Table
        rowKey={rowKey}
        className={cx(styles.root, className)}
        columns={columns}
        data={data}
        expandable={expandableFn}
        rowClassName={(_record, index) => (index % 2 === 0 ? styles.rowEven : '')}
        {...restProps}
      />
      {pagination && (
        <div className={styles.pagination}>
          <Pagination hideWhenSinglePage currentPage={page} numberOfPages={numberOfPages} onNavigate={onNavigate} />
        </div>
      )}
    </VerticalGroup>
  );
};
