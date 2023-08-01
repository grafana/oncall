import React, { useCallback, useState } from 'react';

import { Button, Field, HorizontalGroup, RadioButtonGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { get } from 'lodash-es';
import { observer } from 'mobx-react';

import Block from 'components/GBlock/Block';
import MonacoEditor from 'components/MonacoEditor/MonacoEditor';
import Text from 'components/Text/Text';
import IncidentMatcher from 'containers/IncidentMatcher/IncidentMatcher';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { ChannelFilter, FilteringTermType } from 'models/channel_filter/channel_filter.types';
import { useStore } from 'state/useStore';
import { openErrorNotification } from 'utils';

import styles from './ChannelFilterForm.module.css';

const cx = cn.bind(styles);

interface ChannelFilterFormProps {
  id: ChannelFilter['id'] | 'new';
  alertReceiveChannelId: AlertReceiveChannel['id'];
  onHide: () => void;
  onUpdate: (channelFilterId: ChannelFilter['id']) => void;
  data?: ChannelFilter;
  className?: string;
}

const ChannelFilterForm = observer((props: ChannelFilterFormProps) => {
  const { id, alertReceiveChannelId, onHide, onUpdate, data, className } = props;

  // TODO: use FilteringTermType.jinja2 instead of 1
  const [filteringTermType, setFilteringTermType] = useState<FilteringTermType>(data ? data.filtering_term_type : 1);

  function renderFilteringTermValue(type) {
    if (data && type === data?.filtering_term_type) {
      return data.filtering_term;
    }
    switch (type) {
      // TODO: use FilteringTermType.regex and jinja2 instead of 0 and 1
      case 0:
        return '.*';
      case 1:
        return '{{ (payload.severity == "foo" and "bar" in payload.region) or True }}';
      default:
        return null;
    }
  }

  const [filteringTerm, setFilteringTerm] = useState<string>(renderFilteringTermValue(filteringTermType));

  const [errors, setErrors] = useState<{ filtering_term?: string }>({});

  const store = useStore();

  const { alertReceiveChannelStore } = store;

  const handleFilteringTermChange = useCallback((value: string) => {
    setErrors({});
    setFilteringTerm(value);
  }, []);

  const onUpdateClickCallback = useCallback(() => {
    (id === 'new'
      ? alertReceiveChannelStore.createChannelFilter({
          alert_receive_channel: alertReceiveChannelId,
          filtering_term: filteringTerm,
          filtering_term_type: filteringTermType,
        })
      : alertReceiveChannelStore.saveChannelFilter(id, {
          filtering_term: filteringTerm,
          filtering_term_type: filteringTermType,
        })
    )
      .then((channelFilter: ChannelFilter) => {
        onUpdate(channelFilter.id);
        onHide();
      })
      .catch((err) => {
        const errors = get(err, 'response.data');
        setErrors(errors);
        if (errors?.non_field_errors) {
          openErrorNotification(errors.non_field_errors);
        }
      });
  }, [filteringTerm, filteringTermType]);

  return (
    <Block bordered className={cx('root', className)}>
      <Text.Title level={4} strong type="primary">
        {id === 'new' ? 'New' : 'Update'} Route
      </Text.Title>
      <Text type="secondary">
        Route sends alert group to a different escalation chain (slack channel, different users, different urgency)
        based on the alert group content.
      </Text>
      <div className={styles.form}>
        <Field>
          <RadioButtonGroup
            options={[
              { label: 'Jinja2 (recommended)', value: 1 },
              { label: 'Regular Expression', value: 0 },
            ]}
            value={filteringTermType}
            onChange={(value) => {
              setErrors({});
              setFilteringTermType(value);
              setFilteringTerm(renderFilteringTermValue(value));
            }}
          />
        </Field>

        {filteringTermType === 0 ? (
          <>
            <Field
              invalid={Boolean(errors['filtering_term'])}
              disabled={data?.is_default}
              error={errors['filtering_term']}
              label="Regex to route alert groups"
              description={
                <>
                  Use{' '}
                  <a href="https://regex101.com/" target="_blank" rel="noreferrer">
                    python style
                  </a>{' '}
                  regex to filter incidents based on a expression
                </>
              }
            >
              <MonacoEditor
                value={filteringTerm}
                disabled={false}
                onChange={handleFilteringTermChange}
                data={{}}
                loading={null}
              />
            </Field>
            {!data?.is_default && (
              <IncidentMatcher
                regexp={filteringTerm}
                className={cx('incident-matcher')}
                onError={(message: string) => {
                  setErrors({ filtering_term: message });
                }}
              />
            )}
          </>
        ) : (
          <>
            <Text type="secondary">
              If the result of the{' '}
              <a href="https://jinja.palletsprojects.com/en/3.0.x/" target="_blank" rel="noreferrer">
                Jinja2-based template
              </a>{' '}
              is <Text keyboard>True</Text>
              alert group will be matched with this route
            </Text>
            <Field
              invalid={Boolean(errors['filtering_term'])}
              disabled={data?.is_default}
              error={errors['filtering_term']}
            >
              <MonacoEditor
                value={filteringTerm}
                disabled={false}
                onChange={handleFilteringTermChange}
                data={{}}
                loading={null}
              />
            </Field>
          </>
        )}
      </div>
      <HorizontalGroup>
        <Button variant="primary" onClick={onUpdateClickCallback}>
          {id === 'new' ? 'Create' : 'Update'} route
        </Button>
        <Button variant="secondary" onClick={onHide}>
          Cancel
        </Button>
      </HorizontalGroup>
    </Block>
  );
});

export default ChannelFilterForm;
