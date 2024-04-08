import React, { useCallback, useMemo, ChangeEvent, ReactElement } from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Pagination, Checkbox, Icon, useStyles2 } from '@grafana/ui';
import Table from 'rc-table';
import { TableProps } from 'rc-table/lib/Table';
import { DefaultRecordType } from 'rc-table/lib/interface';

export interface GTableProps<RecordType = unknown> extends TableProps<RecordType> {
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
  showHeader?: boolean;
}

export const GTable = <RT extends DefaultRecordType = DefaultRecordType>(props: GTableProps<RT>): ReactElement => {
  const {
    columns: columnsProp,
    data,
    className,
    pagination,
    rowSelection,
    rowKey,
    expandable,
    showHeader = true,
    ...restProps
  } = props;

  const styles = useStyles2(getGTableStyles);

  if (expandable) {
    expandable.expandIcon = (props: { expanded: boolean; record: any }) => {
      const { expanded, record } = props;
      return (
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
      );
    };
  }

  const { page, total: numberOfPages, onChange: onNavigate } = pagination || {};

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
        width: '40px',
        key: 'check',
        title: (
          <Checkbox
            className={cx(styles.checkbox)}
            onChange={handleMasterCheckboxChange}
            value={data?.length > 0 && rowSelection.selectedRowKeys.length === data?.length}
          />
        ),
        render: (item: any) => {
          return (
            <Checkbox
              className={cx(styles.checkbox)}
              value={rowSelection.selectedRowKeys.includes(item[rowKey as string])}
              onChange={getCheckboxClickHandler(item[rowKey as string])}
            />
          );
        },
      });
    }
    return columns;
  }, [rowSelection, columnsProp, data]);

  return (
    <div className={cx(styles.root)} data-testid="test__gTable">
      <Table<RT>
        expandable={expandable}
        rowKey={rowKey}
        // .filter-table is grafana-wide classname
        className={cx('filter-table', className)}
        columns={columns}
        data={data}
        showHeader={showHeader}
        {...restProps}
      />
      {pagination && (
        <div className={cx(styles.pagination)}>
          <Pagination hideWhenSinglePage currentPage={page} numberOfPages={numberOfPages} onNavigate={onNavigate} />
        </div>
      )}
    </div>
  );
};

const getGTableStyles = (_theme: GrafanaTheme2) => {
  return {
    root: css`
      table {
        width: 100%;
      }
    `,

    pagination: css`
      margin-top: 20px;
    `,

    checkbox: css`
      display: inline-flex;
    `,
  };
};
