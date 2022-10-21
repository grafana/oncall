import React, { FC, useCallback, useMemo, ChangeEvent } from 'react';

import { Pagination, Checkbox, Icon } from '@grafana/ui';
import cn from 'classnames/bind';
import Table from 'rc-table';
import { TableProps } from 'rc-table/lib/Table';

import styles from './GTable.module.css';

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
    onExpandedRowsChange: (rows: string[]) => void;
    expandRowByClick: boolean;
    expandIcon?: (props: { expanded: boolean; record: any }) => React.ReactNode;
    onExpand?: (expanded: boolean, item: any) => void;
  };
}

const GTable: FC<Props> = ({
  columns: columnsProp,
  data,
  className,
  pagination,
  loading,
  rowSelection,
  rowKey,
  expandable,
  ...restProps
}) => {
  const { page, total: numberOfPages, onChange: onNavigate } = pagination || {};

  const expandIcon = useCallback(
    ({ expanded, record }: { expanded: boolean; record: any }) => (
      <Icon
        style={{ cursor: 'pointer' }}
        name={expanded ? 'angle-down' : 'angle-right'}
        onClick={(event) => {
          event.stopPropagation();

          const newExpanded = !expanded;
          const newExpandedRowKeys = [...expandable.expandedRowKeys];
          if (newExpanded && !expandable.expandedRowKeys.includes(record[rowKey as string])) {
            newExpandedRowKeys.push(record[rowKey as string]);
          } else if (!newExpanded && expandable.expandedRowKeys.includes(record[rowKey as string])) {
            const index = newExpandedRowKeys.indexOf(record[rowKey as string]);
            newExpandedRowKeys.splice(index, 1);
          }

          expandable.onExpand && expandable.onExpand(newExpanded, record);
          expandable.onExpandedRowsChange(newExpandedRowKeys);
        }}
      />
    ),
    [expandable, rowKey]
  );

  const getCheckboxClickHandler = useCallback(
    (id: string) => {
      const { selectedRowKeys, onChange } = rowSelection;

      return (event: ChangeEvent<HTMLInputElement>) => {
        const checked = event.target.checked;

        const newSelectedRowKeys = [...selectedRowKeys];

        if (!checked && newSelectedRowKeys.includes(id)) {
          const index = newSelectedRowKeys.indexOf(id);
          newSelectedRowKeys.splice(index, 1);
        } else if (checked) {
          newSelectedRowKeys.push(id);
        }

        onChange(newSelectedRowKeys);
      };
    },
    [rowSelection]
  );

  const handleMasterCheckboxChange = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      const { onChange } = rowSelection;
      if (event.target.checked) {
        const newRowSelection = data.map((item: any) => item[rowKey as string]);
        onChange(newRowSelection);
      } else {
        onChange([]);
      }
    },
    [data]
  );

  const columns = useMemo(() => {
    const columns = [...columnsProp];

    if (rowSelection) {
      columns.unshift({
        width: '25px',
        key: 'check',
        title: (
          <Checkbox
            className={cx('checkbox')}
            onChange={handleMasterCheckboxChange}
            value={data?.length > 0 && rowSelection.selectedRowKeys.length === data?.length}
          />
        ),
        render: (item: any) => {
          return (
            <Checkbox
              className={cx('checkbox')}
              value={rowSelection.selectedRowKeys.includes(item[rowKey as string])}
              onChange={getCheckboxClickHandler(item[rowKey as string])}
            />
          );
        },
      });
    }
    return columns;
  }, [rowSelection, columnsProp, data]);

  if (expandable) {
    expandable.expandIcon = expandIcon;
  }

  return (
    <div className={cx('root')} data-testid="test__gTable">
      <Table
        expandable={expandable}
        rowKey={rowKey}
        className={cx('filter-table', className)}
        columns={columns}
        data={data}
        {...restProps}
      />
      {pagination && (
        <div className={cx('pagination')}>
          <Pagination hideWhenSinglePage currentPage={page} numberOfPages={numberOfPages} onNavigate={onNavigate} />
        </div>
      )}
    </div>
  );
};

export default GTable;
