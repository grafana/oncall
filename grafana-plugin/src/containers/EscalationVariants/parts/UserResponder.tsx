import React, { FC } from 'react';

import { HorizontalGroup, Icon, Select, IconButton, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';

import Avatar from 'components/Avatar/Avatar';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import styles from 'containers/EscalationVariants/EscalationVariants.module.scss';
import {
  ResponderBaseProps,
  UserResponder as UserResponderType,
} from 'containers/EscalationVariants/EscalationVariants.types';

const cx = cn.bind(styles);

type UserResponderProps = ResponderBaseProps & Pick<UserResponderType, 'important' | 'data'>;

const UserResponder: FC<UserResponderProps> = ({ important, data, onImportantChange, handleDelete }) => (
  <li>
    <HorizontalGroup justify="space-between">
      <HorizontalGroup>
        <div className={cx('timeline-icon-background', { 'timeline-icon-background--green': true })}>
          <Avatar size="medium" src={data?.avatar} />
        </div>
        <Text className={cx('responder-name')}>{data?.username}</Text>
        {data.notification_chain_verbal.default || data.notification_chain_verbal.important ? (
          <HorizontalGroup>
            <Text type="secondary">by</Text>
            <Select
              className={cx('select')}
              width="auto"
              isSearchable={false}
              value={Number(important)}
              options={[
                {
                  value: 0,
                  label: 'Default',
                  description: 'Use "Default notifications" from user\'s personal settings',
                },
                {
                  value: 1,
                  label: 'Important',
                  description: 'Use "Important notifications" from user\'s personal settings',
                },
              ]}
              // @ts-ignore
              isOptionDisabled={({ value }) =>
                (value === 0 && !data.notification_chain_verbal.default) ||
                (value === 1 && !data.notification_chain_verbal.important)
              }
              getOptionLabel={({ value, label }) => {
                return (
                  <Text
                    type={
                      (value === 0 && !data.notification_chain_verbal.default) ||
                      (value === 1 && !data.notification_chain_verbal.important)
                        ? 'disabled'
                        : 'primary'
                    }
                  >
                    {label}
                  </Text>
                );
              }}
              onChange={onImportantChange}
            />
            <Text type="secondary">notification policies</Text>
          </HorizontalGroup>
        ) : (
          <HorizontalGroup>
            <Tooltip content="User doesn't have configured notification policies">
              <Icon name="exclamation-triangle" style={{ color: 'var(--error-text-color)' }} />
            </Tooltip>
          </HorizontalGroup>
        )}
      </HorizontalGroup>
      <HorizontalGroup>
        <PluginLink className={cx('hover-button')} target="_blank" query={{ page: 'users', id: data.pk }}>
          <IconButton
            tooltip="Open user profile in new tab"
            style={{ color: 'var(--always-gray)' }}
            name="external-link-alt"
          />
        </PluginLink>
        <IconButton tooltip="Remove responder" className={cx('hover-button')} name="trash-alt" onClick={handleDelete} />
      </HorizontalGroup>
    </HorizontalGroup>
  </li>
);

export default UserResponder;
