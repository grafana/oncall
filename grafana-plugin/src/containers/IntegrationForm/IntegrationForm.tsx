import React, { useState, ChangeEvent } from 'react';

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
  Label,
} from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import { useHistory } from 'react-router-dom';

import Collapse from 'components/Collapse/Collapse';
import Block from 'components/GBlock/Block';
import GForm from 'components/GForm/GForm';
import { FormItem } from 'components/GForm/GForm.types';
import IntegrationLogo from 'components/IntegrationLogo/IntegrationLogo';
import Text from 'components/Text/Text';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import {
  AlertReceiveChannel,
  AlertReceiveChannelOption,
} from 'models/alert_receive_channel/alert_receive_channel.types';
import { useStore } from 'state/useStore';
import { openErrorNotification } from 'utils';
import { UserActions } from 'utils/authorization';
import { PLUGIN_ROOT } from 'utils/consts';

import { form } from './IntegrationForm.config';
import { prepareForEdit } from './IntegrationForm.helpers';
import styles from './IntegrationForm.module.scss';

const cx = cn.bind(styles);

interface IntegrationFormProps {
  id: AlertReceiveChannel['id'] | 'new';
  isTableView?: boolean;
  onHide: () => void;
  onUpdate: () => void;
}

const IntegrationForm = observer((props: IntegrationFormProps) => {
  const store = useStore();
  const history = useHistory();

  const { id, onHide, onUpdate, isTableView = true } = props;
  const {
    alertReceiveChannelStore,
    userStore: { currentUser: user },
  } = store;

  const [filterValue, setFilterValue] = useState('');
  const [showNewIntegrationForm, setShowNewIntegrationForm] = useState(false);
  const [selectedOption, setSelectedOption] = useState<AlertReceiveChannelOption>(undefined);
  const [showIntegrarionsListDrawer, setShowIntegrarionsListDrawer] = useState(id === 'new');

  const data =
    id === 'new'
      ? { integration: selectedOption?.value, team: user?.current_team }
      : prepareForEdit(alertReceiveChannelStore.items[id]);

  const { alertReceiveChannelOptions } = alertReceiveChannelStore;

  const options = alertReceiveChannelOptions
    ? alertReceiveChannelOptions.filter(
        (option: AlertReceiveChannelOption) =>
          option.display_name.toLowerCase().includes(filterValue.toLowerCase()) &&
          !option.value.toLowerCase().startsWith('legacy_')
      )
    : [];

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
              <GForm
                form={form}
                data={data}
                customFieldSectionRenderer={CustomFieldSectionRenderer}
                onSubmit={handleSubmit}
              />

              {isTableView && <HowTheIntegrationWorks selectedOption={selectedOption} />}

              <HorizontalGroup justify="flex-end">
                {id === 'new' ? (
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setShowNewIntegrationForm(false);
                      setShowIntegrarionsListDrawer(true);
                    }}
                  >
                    Back
                  </Button>
                ) : (
                  <Button variant="secondary" onClick={onHide}>
                    Cancel
                  </Button>
                )}

                <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                  <Button form={form.name} type="submit" data-testid="update-integration-button">
                    {id === 'new' ? 'Create' : 'Update'} Integration
                  </Button>
                </WithPermissionControlTooltip>
              </HorizontalGroup>
            </VerticalGroup>
          </div>
        </Drawer>
      )}
    </>
  );

  function handleSubmit(data: Partial<AlertReceiveChannel>) {
    (id === 'new'
      ? alertReceiveChannelStore
          .create(data)
          .then((response) => {
            history.push(`${PLUGIN_ROOT}/integrations/${response.id}`);
          })
          .catch(onCatch)
      : alertReceiveChannelStore.update(id, data)
    ).then(() => {
      onHide();
      onUpdate();
    });

    function onCatch(err: any) {
      if (err.response?.data?.length > 0) {
        openErrorNotification(err.response.data);
      } else {
        openErrorNotification('Something went wrong, please try again later.');
      }
    }
  }

  function onBlockClick(option: AlertReceiveChannelOption) {
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

export interface CustomFieldSectionRendererProps {
  control: any;
  formItem: FormItem;
  onChange: (field: any, value: any) => void;
}

const CustomFieldSectionRenderer: React.FC<CustomFieldSectionRendererProps> = ({ control, formItem, onChange }) => {
  console.log({ control, formItem, onChange });

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

  const [selectedRadioOption, setSelectedRadioOption] = useState<string>(radioOptions[0].value);
  const [selectedAlertManagerOption, setSelectedAlertManagerOption] = useState<string>();
  const [selectedContactPointOption, setSelectedContactPointOption] = useState<string>();

  const selectOptions = [];

  return (
    <div className={cx('extra-fields')}>
      <VerticalGroup spacing="md">
        <HorizontalGroup spacing="xs" align="center">
          <Label>Grafana Alerting Contact point</Label>
          <Icon name="info-circle" className={cx('extra-fields__icon')} />
        </HorizontalGroup>

        <div className={cx('extra-fields__radio')}>
          <RadioButtonGroup
            options={radioOptions}
            value={selectedRadioOption}
            onChange={(radioValue) => setSelectedRadioOption(radioValue)}
          />
        </div>

        <Select
          options={selectOptions}
          onChange={onAlertManagerChange}
          value={selectedAlertManagerOption}
          placeholder="Select Alert Manager"
        />
        <Select
          options={selectOptions}
          onChange={onContactPointChange}
          value={selectedContactPointOption}
          placeholder="Select Contact Point"
        />
      </VerticalGroup>
    </div>
  );

  function onAlertManagerChange(option: SelectableValue<string>) {
    setSelectedAlertManagerOption(option.value);
  }

  function onContactPointChange(option: SelectableValue<string>) {
    setSelectedContactPointOption(option.value);
  }
};

const HowTheIntegrationWorks: React.FC<{ selectedOption: AlertReceiveChannelOption }> = ({ selectedOption }) => {
  if (!selectedOption) {
    return null;
  }

  return (
    <Collapse
      headerWithBackground
      className={cx('collapse')}
      isOpen={false}
      label={<Text type="link">How the integration works</Text>}
      contentClassName={cx('collapsable-content')}
    >
      <Text type="secondary">
        The integration will generate the following:
        <ul className={cx('integration-info-list')}>
          <li className={cx('integration-info-item')}>Unique URL endpoint for receiving alerts </li>
          <li className={cx('integration-info-item')}>
            Templates to interpret alerts, tailored for {selectedOption.display_name}{' '}
          </li>
          <li className={cx('integration-info-item')}>{selectedOption.display_name} contact point </li>
          <li className={cx('integration-info-item')}>{selectedOption.display_name} notification</li>
        </ul>
        What you’ll need to do next:
        <ul className={cx('integration-info-list')}>
          <li className={cx('integration-info-item')}>
            Finish connecting Monitoring system using Unique URL that will be provided on the next step{' '}
          </li>
          <li className={cx('integration-info-item')}>
            Set up routes that are based on alert content, such as severity, region, and service{' '}
          </li>
          <li className={cx('integration-info-item')}>Connect escalation chains to the routes</li>
          <li className={cx('integration-info-item')}>
            Review templates and personalize according to your requirements
          </li>
        </ul>
      </Text>
    </Collapse>
  );
};

const IntegrationBlocks: React.FC<{
  options: AlertReceiveChannelOption[];
  onBlockClick: (option: AlertReceiveChannelOption) => void;
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

export default IntegrationForm;
