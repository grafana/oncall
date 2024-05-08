import React, { useState, ChangeEvent } from 'react';

import { Drawer, VerticalGroup, HorizontalGroup, Input, Tag, EmptySearchResult } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { Block } from 'components/GBlock/Block';
import { IntegrationLogo } from 'components/IntegrationLogo/IntegrationLogo';
import { Text } from 'components/Text/Text';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

import { IntegrationForm } from './IntegrationForm';
import styles from './IntegrationFormContainer.module.scss';

const cx = cn.bind(styles);

interface IntegrationFormContainerProps {
  id: ApiSchemas['AlertReceiveChannel']['id'] | 'new';
  isTableView?: boolean;
  onHide: () => void;
  onSubmit: () => Promise<void>;
  navigateToAlertGroupLabels: (id: ApiSchemas['AlertReceiveChannel']['id']) => void;
}

export const IntegrationFormContainer = observer((props: IntegrationFormContainerProps) => {
  const store = useStore();

  const { id, onHide, onSubmit, isTableView = true, navigateToAlertGroupLabels } = props;
  const { alertReceiveChannelStore } = store;

  const [filterValue, setFilterValue] = useState('');
  const [showNewIntegrationForm, setShowNewIntegrationForm] = useState(false);
  const [selectedOption, setSelectedOption] = useState<ApiSchemas['AlertReceiveChannelIntegrationOptions']>(undefined);
  const [showIntegrationsListDrawer, setshowIntegrationsListDrawer] = useState(id === 'new');

  const { alertReceiveChannelOptions } = alertReceiveChannelStore;

  const options = alertReceiveChannelOptions
    ? alertReceiveChannelOptions.filter((option: ApiSchemas['AlertReceiveChannelIntegrationOptions']) => {
        if (option.value === 'grafana_alerting' && !window.grafanaBootData.settings.unifiedAlertingEnabled) {
          return false;
        }

        // don't allow creating direct paging integrations
        if (option.value === 'direct_paging') {
          return false;
        }

        return (
          option.display_name.toLowerCase().includes(filterValue.toLowerCase()) &&
          !option.value.toLowerCase().startsWith('legacy_')
        );
      })
    : [];

  return (
    <>
      {showIntegrationsListDrawer && (
        <Drawer scrollableContent title="New Integration" onClose={onHide} closeOnMaskClick={false} width="640px">
          <div className={cx('content')}>
            <VerticalGroup>
              <Text type="secondary">
                Integration receives alerts on an unique API URL, interprets them using set of templates tailored for
                monitoring system and starts escalations.
              </Text>

              <div className={cx('search-integration')}>
                <Input
                  autoFocus
                  value={filterValue}
                  placeholder="Search integrations ..."
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setFilterValue(e.currentTarget.value)}
                />
              </div>

              <IntegrationBlocks options={options} onBlockClick={onBlockClick} />
            </VerticalGroup>
          </div>
        </Drawer>
      )}
      {(showNewIntegrationForm || !showIntegrationsListDrawer) && (
        <Drawer scrollableContent title={getTitle()} onClose={onHide} closeOnMaskClick={false} width="640px">
          <div className={cx('content')}>
            <VerticalGroup>
              <IntegrationForm
                id={id}
                onBackClick={onBackClick}
                navigateToAlertGroupLabels={navigateToAlertGroupLabels}
                selectedIntegration={selectedOption}
                onSubmit={onSubmit}
                onHide={onHide}
              />
            </VerticalGroup>
          </div>
        </Drawer>
      )}
    </>
  );

  function onBackClick(): void {
    setShowNewIntegrationForm(false);
    setshowIntegrationsListDrawer(true);
  }

  function onBlockClick(option: ApiSchemas['AlertReceiveChannelIntegrationOptions']): void {
    setSelectedOption(option);
    setShowNewIntegrationForm(true);
    setshowIntegrationsListDrawer(false);
  }

  function getTitle(): string {
    if (!isTableView) {
      return 'Integration Settings';
    }

    return id === 'new' ? `New ${selectedOption?.display_name} integration` : `Edit integration`;
  }
});

const IntegrationBlocks: React.FC<{
  options: Array<ApiSchemas['AlertReceiveChannelIntegrationOptions']>;
  onBlockClick: (option: ApiSchemas['AlertReceiveChannelIntegrationOptions']) => void;
}> = ({ options, onBlockClick }) => {
  return (
    <div className={cx('cards')} data-testid="create-integration-modal">
      {options.length ? (
        options.map((alertReceiveChannelChoice) => {
          return (
            <Block
              bordered
              hover
              shadowed
              onClick={() => onBlockClick(alertReceiveChannelChoice)}
              key={alertReceiveChannelChoice.value}
              className={cx('card', { card_featured: alertReceiveChannelChoice.featured })}
            >
              <div className={cx('card-bg')}>
                <IntegrationLogo integration={alertReceiveChannelChoice} scale={0.2} />
              </div>
              <div className={cx('title')}>
                <VerticalGroup spacing={alertReceiveChannelChoice.featured ? 'xs' : 'none'}>
                  <HorizontalGroup>
                    <Text strong data-testid="integration-display-name">
                      {alertReceiveChannelChoice.display_name}
                    </Text>
                    {alertReceiveChannelChoice.featured && alertReceiveChannelChoice.featured_tag_name && (
                      <Tag name={alertReceiveChannelChoice.featured_tag_name} colorIndex={5} />
                    )}
                  </HorizontalGroup>
                  <Text type="secondary" size="small">
                    {alertReceiveChannelChoice.short_description}
                  </Text>
                </VerticalGroup>
              </div>
            </Block>
          );
        })
      ) : (
        <EmptySearchResult>Could not find anything matching your query</EmptySearchResult>
      )}
    </div>
  );
};
