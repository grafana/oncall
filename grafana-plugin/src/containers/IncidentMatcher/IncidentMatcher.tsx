import React, { useEffect, useState, useCallback } from 'react';

import { EmptySearchResult, LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Block from 'components/GBlock/Block';
import SourceCode from 'components/SourceCode/SourceCode';
import Text from 'components/Text/Text';
import { Alert } from 'models/alertgroup/alertgroup.types';
import { makeRequest } from 'network';
import { useStore } from 'state/useStore';
import { useDebouncedCallback } from 'utils/hooks';

import styles from 'containers/IncidentMatcher/IncidentMatcher.module.css';

const cx = cn.bind(styles);

interface IncidentMatcherProps {
  regexp: string;
  className?: string;
  onError: (message: string) => void;
}

interface AlertItem {
  pk: Alert['pk'];
  title: Alert['title'];
  payload: any;
  inside_organization_number: number;
}

const IncidentMatcher = observer((props: IncidentMatcherProps) => {
  const { regexp, className, onError } = props;

  const store = useStore();

  const [searchResult, setSearchResult] = useState<AlertItem[] | undefined>(undefined);
  const [isLoading, setLoading] = useState<boolean | undefined>(false);
  const [selectedAlertItem, setSelectedAlertItem] = useState<AlertItem | undefined>(undefined);

  const {} = store;

  const handleRegexpChange = useDebouncedCallback(() => {
    setLoading(true);
    makeRequest('/route_regex_debugger/', { params: { regex: regexp } })
      .then(setSearchResult)
      .catch((data) => {
        onError(data.response?.data?.detail);
      })
      .finally(() => setLoading(false));
  }, 1000);

  useEffect(handleRegexpChange, [regexp]);

  const getIncidentClickHandler = useCallback((item: AlertItem) => {
    return () => {
      setSelectedAlertItem(item);
    };
  }, []);

  return (
    <Block bordered className={cx('root', className)} withBackground>
      <div className={cx('columns')}>
        <div className={cx('incident-list')}>
          <Text.Title className={cx('title')} level={5}>
            Matching Alert Groups
          </Text.Title>
          {isLoading ? (
            <LoadingPlaceholder text="Loading..." />
          ) : (
            <>
              {searchResult ? (
                searchResult.length ? (
                  <ul className={cx('incident-item-list')}>
                    {searchResult.map((item) => (
                      <li key={item.pk}>
                        <Text
                          type="link"
                          strong={selectedAlertItem && selectedAlertItem.pk === item.pk}
                          onClick={getIncidentClickHandler(item)}
                        >
                          #{item.inside_organization_number} {item.title}
                          {selectedAlertItem && selectedAlertItem.pk === item.pk && ' 👉'}
                        </Text>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <EmptySearchResult>Could not find anything matching your query</EmptySearchResult>
                )
              ) : (
                <LoadingPlaceholder text="Loading..." />
              )}
            </>
          )}
        </div>
        <div className={cx('incident-payload')}>
          <Text.Title className={cx('title')} level={5}>
            Alert Group payload
          </Text.Title>
          {selectedAlertItem ? (
            <SourceCode noMaxHeight>{JSON.stringify(selectedAlertItem, null, 2)}</SourceCode>
          ) : (
            <Text type="secondary">← Select alert group first</Text>
          )}
        </div>
      </div>
    </Block>
  );
});

export default IncidentMatcher;
