import React, { FC } from 'react';

import { HorizontalGroup, Select, IconButton } from '@grafana/ui';
import cn from 'classnames/bind';

import Avatar from 'components/Avatar/Avatar';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import styles from 'containers/EscalationVariants/EscalationVariants.module.scss';
import {
  ResponderBaseProps,
  TeamResponder as TeamResponderType,
} from 'containers/EscalationVariants/EscalationVariants.types';

const cx = cn.bind(styles);

type TeamResponderProps = ResponderBaseProps & Pick<TeamResponderType, 'important' | 'data'>;

const TeamResponder: FC<TeamResponderProps> = ({ important, data, onImportantChange, handleDelete }) => (
  <li>
    <HorizontalGroup justify="space-between">
      <HorizontalGroup>
        <div className={cx('timeline-icon-background')}>
          <Avatar size="medium" src={data?.avatar_url} />
        </div>
        <Text className={cx('responder-name')}>{data.name}</Text>
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
              description: 'Use "Default notifications" from users personal settings',
            },
            {
              value: 1,
              label: 'Important',
              description: 'Use "Important notifications" from users personal settings',
            },
          ]}
          onChange={onImportantChange}
        />
        <Text type="secondary">notification policies</Text>
      </HorizontalGroup>
      <HorizontalGroup>
        <PluginLink className={cx('hover-button')} target="_blank" query={{ page: 'schedules', id: data.id }}>
          <IconButton
            tooltip="Open schedule in new tab"
            style={{ color: 'var(--always-gray)' }}
            name="external-link-alt"
          />
        </PluginLink>
        <IconButton className={cx('hover-button')} tooltip="Remove responder" name="trash-alt" onClick={handleDelete} />
      </HorizontalGroup>
    </HorizontalGroup>
  </li>
);

export default TeamResponder;
