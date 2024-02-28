import React, { useState, ChangeEvent, useEffect, useReducer, useRef, useMemo } from 'react';

import { SelectableValue } from '@grafana/data';
import {
  Drawer,
  VerticalGroup,
  HorizontalGroup,
  Input,
  Tag,
  EmptySearchResult,
  Button,
  RadioButtonGroup,
  Select,
  Icon,
  Field,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { Block } from 'components/GBlock/Block';
import { CustomFieldSectionRendererProps, GForm } from 'components/GForm/GForm';
import { IntegrationLogo } from 'components/IntegrationLogo/IntegrationLogo';
import { Text } from 'components/Text/Text';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { IntegrationHelper } from 'pages/integration/Integration.helper';
import { useStore } from 'state/useStore';

import { HookForm } from './HookForm';
import styles from './IntegrationForm.module.scss';

const cx = cn.bind(styles);

interface IntegrationFormProps {
  id: ApiSchemas['AlertReceiveChannel']['id'] | 'new';
  isTableView?: boolean;
  onHide: () => void;
  onSubmit: () => Promise<void>;
  navigateToAlertGroupLabels: (id: ApiSchemas['AlertReceiveChannel']['id']) => void;
}

export const IntegrationForm = observer((props: IntegrationFormProps) => {
  const store = useStore();

  const { id, onHide, onSubmit, isTableView = true, navigateToAlertGroupLabels } = props;
  const { alertReceiveChannelStore, grafanaTeamStore } = store;

  const [filterValue, setFilterValue] = useState('');
  const [showNewIntegrationForm, setShowNewIntegrationForm] = useState(false);
  const [selectedOption, setSelectedOption] = useState<ApiSchemas['AlertReceiveChannelIntegrationOptions']>(undefined);
  const [showIntegrarionsListDrawer, setShowIntegrarionsListDrawer] = useState(id === 'new');

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

  const extraGFormProps: { customFieldSectionRenderer?: React.FC<CustomFieldSectionRendererProps> } = {};

  if (selectedOption && IntegrationHelper.isSpecificIntegration(selectedOption.value, 'grafana_alerting')) {
    extraGFormProps.customFieldSectionRenderer = CustomFieldSectionRenderer;
  }

  return (
    <>
      {showIntegrarionsListDrawer && (
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
      {(showNewIntegrationForm || !showIntegrarionsListDrawer) && (
        <Drawer scrollableContent title={getTitle()} onClose={onHide} closeOnMaskClick={false} width="640px">
          <div className={cx('content')}>
            <VerticalGroup>
              <HookForm
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
    setShowIntegrarionsListDrawer(true);
  }

  function onBlockClick(option: ApiSchemas['AlertReceiveChannelIntegrationOptions']): void {
    setSelectedOption(option);
    setShowNewIntegrationForm(true);
    setShowIntegrarionsListDrawer(false);
  }

  function getTitle(): string {
    if (!isTableView) {
      return 'Integration Settings';
    }

    return id === 'new' ? `New ${selectedOption?.display_name} integration` : `Edit integration`;
  }
});

interface CustomFieldSectionRendererState {
  isExistingContactPoint: boolean;
  selectedAlertManagerOption: string;
  selectedContactPointOption: string;

  dataSources: Array<{ label: string; value: string }>;
  contactPoints: Array<{ label: string; value: string }>;
  allContactPoints: Array<{ name: string; uid: string; contact_points: string[] }>;
}

const CustomFieldSectionRenderer: React.FC<CustomFieldSectionRendererProps> = ({
  control: _control,
  formItem: _formItem,
  errors,
  register,
  setValue,
}) => {
  const radioOptions = [
    {
      label: 'Connect existing Contact point',
      value: 'existing',
    },
    {
      label: 'Create a new one',
      value: 'new',
    },
  ];

  const [
    {
      isExistingContactPoint,
      dataSources,
      contactPoints,
      selectedAlertManagerOption,
      selectedContactPointOption,
      allContactPoints,
    },
    setState,
  ] = useReducer(
    (state: CustomFieldSectionRendererState, newState: Partial<CustomFieldSectionRendererState>) => ({
      ...state,
      ...newState,
    }),
    {
      isExistingContactPoint: true,
      selectedAlertManagerOption: undefined,
      selectedContactPointOption: undefined,
      dataSources: [],
      contactPoints: [],
      allContactPoints: [],
    }
  );

  useEffect(() => {
    (async function () {
      const response = await AlertReceiveChannelHelper.getGrafanaAlertingContactPoints();
      setState({
        allContactPoints: response,
        dataSources: response.map((res) => ({ label: res.name, value: res.uid })),
        contactPoints: [],
      });
    })();

    setValue('is_existing', true);
  }, []);

  return (
    <div className={cx('extra-fields')}>
      <VerticalGroup spacing="md">
        <HorizontalGroup spacing="xs" align="center">
          <Text type="primary" size="small">
            Grafana Alerting Contact point
          </Text>
          <Icon name="info-circle" />
        </HorizontalGroup>

        <div className={cx('extra-fields__radio')}>
          <RadioButtonGroup
            options={radioOptions}
            value={isExistingContactPoint ? 'existing' : 'new'}
            onChange={(radioValue) => {
              setState({
                isExistingContactPoint: radioValue === 'existing',
                contactPoints: [],
                selectedAlertManagerOption: null,
                selectedContactPointOption: null,
              });

              setValue('is_existing', radioValue === 'existing');
              setValue('alert_manager', undefined);
              setValue('contact_point', undefined);
            }}
          />
        </div>

        <div className={cx('selectors-container')}>
          <Field invalid={!!errors['alert_manager']} error={'Alert Manager is required'}>
            <Select
              {...register('alert_manager', { required: true })}
              options={dataSources}
              onChange={onAlertManagerChange}
              value={selectedAlertManagerOption}
              placeholder="Select Alert Manager"
            />
          </Field>

          <Field invalid={!!errors['contact_point']} error={'Contact Point is required'}>
            {isExistingContactPoint ? (
              <Select
                {...register('contact_point', { required: true })}
                options={contactPoints}
                onChange={onContactPointChange}
                value={selectedContactPointOption}
                placeholder="Select Contact Point"
              />
            ) : (
              <Input
                value={selectedContactPointOption}
                placeholder="Choose Contact Point"
                onChange={({ target }) => {
                  const value = (target as HTMLInputElement).value;
                  setState({ selectedContactPointOption: value });
                  setValue('contact_point', value);
                }}
              />
            )}
          </Field>
        </div>
      </VerticalGroup>
    </div>
  );

  function onAlertManagerChange(option: SelectableValue<string>) {
    const contactPointsForCurrentOption = allContactPoints
      .find((opt) => opt.uid === option.value)
      .contact_points?.map((cp) => ({ value: cp, label: cp }));

    const newState: Partial<CustomFieldSectionRendererState> = {
      selectedAlertManagerOption: option.value,
      contactPoints: contactPointsForCurrentOption,
    };

    if (isExistingContactPoint) {
      newState.selectedContactPointOption = null;
      setValue('contact_point', undefined);
    }

    setState(newState);

    setValue('alert_manager', option.value);
  }

  function onContactPointChange(option: SelectableValue<string>) {
    setState({ selectedContactPointOption: option.value });
    setValue('contact_point', option.value);
  }
};

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
