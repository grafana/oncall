import React, { useCallback, useState, ChangeEvent } from 'react';

import { Button, Field, HorizontalGroup, Input, RadioButtonGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { get } from 'lodash-es';
import { observer } from 'mobx-react';

import Block from 'components/GBlock/Block';
import Text from 'components/Text/Text';
import IncidentMatcher from 'containers/IncidentMatcher/IncidentMatcher';
import { AlertReceiveChannel } from 'models/alert_receive_channel';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
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

  const [filteringTerm, setFilteringTerm] = useState<string>(data ? data.filtering_term : '.*');
  const [filteringTermJinja2, setFilteringTermJinja2] = useState<string>(
    data ? data.filtering_term_jinja2 : '{payload.foo == "bar"}'
  );
  const [filteringTermType, setFilteringTermType] = useState<number>(data ? data.filtering_term_type : 1);
  const [errors, setErrors] = useState<{ filtering_term?: string }>({});

  const store = useStore();

  const { alertReceiveChannelStore } = store;

  const handleFilteringTermChange = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setErrors({});
    setFilteringTerm(event.target.value);
  }, []);

  const handleFilteringTermJinja2Change = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setErrors({});
    setFilteringTermJinja2(event.target.value);
  }, []);

  const onUpdateClickCallback = useCallback(() => {
    (id === 'new'
      ? alertReceiveChannelStore.createChannelFilter({
          order: 0,
          alert_receive_channel: alertReceiveChannelId,
          filtering_term: filteringTerm,
          filtering_term_jinja2: filteringTermJinja2,
          filtering_term_type: filteringTermType,
        })
      : alertReceiveChannelStore.saveChannelFilter(id, {
          filtering_term: filteringTerm,
          filtering_term_jinja2: filteringTermJinja2,
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
  }, [filteringTerm, filteringTermJinja2, filteringTermType]);

  return (
    <Block bordered className={cx('root', className)}>
      <Text.Title level={4} strong type="primary">
        {id === 'new' ? 'New' : 'Update'} Route
      </Text.Title>
      <Text type="secondary">
        Sends alert to a different escalation chain (slack channel, different users, different urgency) based on the
        alert content, using regular expressions.
      </Text>
      <div className={styles.form}>
        <RadioButtonGroup
          options={[
            { label: 'Jinja2 (recommended)', value: 1 },
            { label: 'Regular Expression', value: 0 },
          ]}
          value={filteringTermType}
          onChange={(value) => {
            setFilteringTermType(value);
          }}
        />

        {filteringTermType === 0 ? (
          <Field
            invalid={Boolean(errors['filtering_term'])}
            disabled={data?.is_default}
            error={errors['filtering_term']}
            label="Regex to route incidents"
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
            <Input
              placeholder={
                data?.is_default ? "Default routes can't have a filtering term" : 'Insert your regular expression here'
              }
              autoFocus
              value={filteringTerm}
              onChange={handleFilteringTermChange}
            />
          </Field>
        ) : (
          <Field
            invalid={Boolean(errors['filtering_term_jinja2'])}
            disabled={data?.is_default}
            error={errors['filtering_term_jinja2']}
            label="OR use Jinja2 template to route incidents"
            description={
              <>
                Use{' '}
                <a href="https://jinja2.com/" target="_blank" rel="noreferrer">
                  Jinja2
                </a>{' '}
                template to filter alert groups based on a expression
              </>
            }
          >
            <Input
              placeholder={
                data?.is_default ? "Default routes can't have a filtering term" : 'Insert your regular expression here'
              }
              autoFocus
              value={filteringTermJinja2}
              onChange={handleFilteringTermJinja2Change}
            />
          </Field>
        )}
      </div>
      {!data?.is_default && (
        <IncidentMatcher
          regexp={filteringTerm}
          filteringTermJinja2={filteringTermJinja2}
          className={cx('incident-matcher')}
          onError={(message: string) => {
            setErrors({ filtering_term: message });
          }}
        />
      )}
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
