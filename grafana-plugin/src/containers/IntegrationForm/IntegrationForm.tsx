import React, { useState, ChangeEvent, useEffect, useReducer } from 'react';

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
  Field,
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
import IntegrationHelper from 'pages/integration/Integration.helper';
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
  onSubmit: () => Promise<void>;
}

const IntegrationForm = observer((props: IntegrationFormProps) => {
  const store = useStore();
  const history = useHistory();

  const { id, onHide, onSubmit, isTableView = true } = props;
  const {
    alertReceiveChannelStore,
    userStore: { currentUser: user },
  } = store;

  const [filterValue, setFilterValue] = useState('');
  const [showNewIntegrationForm, setShowNewIntegrationForm] = useState(false);
  const [selectedOption, setSelectedOption] = useState<AlertReceiveChannelOption>(undefined);
  const [showIntegrarionsListDrawer, setShowIntegrarionsListDrawer] = useState(id === 'new');
  const [allContactPoints, setAllContactPoints] = useState([]);

  useEffect(() => {
    (async function () {
      setAllContactPoints(await alertReceiveChannelStore.getGrafanaAlertingContactPoints());
    })();
  }, []);

  const data =
    id === 'new'
      ? { integration: selectedOption?.value, team: user?.current_team }
      : prepareForEdit(alertReceiveChannelStore.items[id]);

  const { alertReceiveChannelOptions } = alertReceiveChannelStore;

  const options = alertReceiveChannelOptions
    ? alertReceiveChannelOptions.filter((option: AlertReceiveChannelOption) => {
        if (option.value === 'grafana_alerting' && !window.grafanaBootData.settings.unifiedAlertingEnabled) {
          return false;
        }

        return (
          option.display_name.toLowerCase().includes(filterValue.toLowerCase()) &&
          !option.value.toLowerCase().startsWith('legacy_')
        );
      })
    : [];

  const extraGFormProps: { customFieldSectionRenderer?: React.FC<CustomFieldSectionRendererProps> } = {};

  if (selectedOption && IntegrationHelper.isGrafanaAlerting(selectedOption.value)) {
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
              <GForm form={form} data={data} onSubmit={handleSubmit} {...extraGFormProps} />

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

  async function handleSubmit(data): Promise<void> {
    const { alert_manager, contact_point, is_existing: isExisting } = data;

    const matchingAlertManager = allContactPoints.find((cp) => cp.uid === alert_manager);
    const hasContactPointInput = alert_manager && contact_point;

    if (
      !isExisting &&
      hasContactPointInput &&
      matchingAlertManager?.contact_points.find((cp) => cp === contact_point)
    ) {
      openErrorNotification('A contact point already exists for this data source');
      return;
    }

    let apiResponseData: void | AlertReceiveChannel;
    const isCreate = id === 'new';

    if (isCreate) {
      apiResponseData = await createNewIntegration();
    } else {
      apiResponseData = await alertReceiveChannelStore.update(id, data);
    }

    if (!apiResponseData) {
      openErrorNotification(
        `There was an issue ${isCreate ? 'creating' : 'updating'} the integration. Please try again.`
      );
      return;
    }

    await onSubmit();
    onHide();

    function createNewIntegration(): Promise<void | AlertReceiveChannel> {
      let promise = alertReceiveChannelStore.create<AlertReceiveChannel>(data);

      const pushHistory = (id) => history.push(`${PLUGIN_ROOT}/integrations/${id}`);

      promise
        .then((response) => {
          if (!response) {
            return;
          }

          if (!IntegrationHelper.isGrafanaAlerting(selectedOption.value)) {
            return pushHistory(response.id);
          }

          return (
            data.is_existing
              ? alertReceiveChannelStore.connectContactPoint(response.id, data.alert_manager, data.contact_point)
              : alertReceiveChannelStore.createContactPoint(response.id, data.alert_manager, data.contact_point)
          )
            .catch(onCatch)
            .finally(() => pushHistory(response.id));
        })
        .catch(onCatch);

      return promise;
    }

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
  errors: any;
  register: any;
  setValue: (fieldName: string, fieldValue: any) => void;
}

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

  const { alertReceiveChannelStore } = useStore();

  useEffect(() => {
    (async function () {
      const response = await alertReceiveChannelStore.getGrafanaAlertingContactPoints();
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
          <Label>Grafana Alerting Contact point</Label>
          <Icon name="info-circle" className={cx('extra-fields__icon')} />
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
        What you'll need to do next:
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
