import React, { FC, useCallback, useState } from 'react';

import { Button, Drawer, HorizontalGroup, Icon, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import Block from 'components/GBlock/Block';
import Text from 'components/Text/Text';
import ScheduleForm from 'containers/ScheduleForm/ScheduleForm';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { Schedule, ScheduleType } from 'models/schedule/schedule.types';
import { UserAction } from 'state/userAction';

import styles from './NewScheduleSelector.module.css';

interface NewScheduleSelectorProps {
  onHide: () => void;
  onCreate: (data: Schedule) => void;
  onUpdate: () => void;
}

const cx = cn.bind(styles);

const NewScheduleSelector: FC<NewScheduleSelectorProps> = (props) => {
  const { onHide, onCreate, onUpdate } = props;

  const [showScheduleForm, setShowScheduleForm] = useState<boolean>(false);
  const [type, setType] = useState<ScheduleType | undefined>();

  const getCreateScheduleClickHandler = useCallback((type: ScheduleType) => {
    return () => {
      setType(type);
      setShowScheduleForm(true);
    };
  }, []);

  return (
    <>
      <Drawer scrollableContent title="Create new schedule" onClose={onHide} closeOnMaskClick>
        <div className={cx('content')}>
          <VerticalGroup spacing="lg">
            <Block bordered withBackground className={cx('block')}>
              <HorizontalGroup justify="space-between">
                <HorizontalGroup spacing="md">
                  <Icon name="calendar-alt" size="xl" />
                  <VerticalGroup spacing="none">
                    <Text type="primary" size="large">
                      Set up on-call rotation schedule
                    </Text>
                    <Text type="secondary">Configure rotations and shifts directly in Grafana On-Call</Text>
                  </VerticalGroup>
                </HorizontalGroup>
                <WithPermissionControl userAction={UserAction.UpdateSchedules}>
                  <Button variant="primary" icon="plus" onClick={getCreateScheduleClickHandler(ScheduleType.API)}>
                    Create
                  </Button>
                </WithPermissionControl>
              </HorizontalGroup>
            </Block>
            <Block bordered withBackground className={cx('block')}>
              <HorizontalGroup justify="space-between">
                <HorizontalGroup spacing="md">
                  <Icon name="download-alt" size="xl" />
                  <VerticalGroup spacing="none">
                    <Text type="primary" size="large">
                      Import schedule from iCal Url
                    </Text>
                    <Text type="secondary">Import rotations and shifts from your calendar app</Text>
                  </VerticalGroup>
                </HorizontalGroup>
                <Button variant="secondary" icon="plus" onClick={getCreateScheduleClickHandler(ScheduleType.Ical)}>
                  Create
                </Button>
              </HorizontalGroup>
            </Block>
            <Block bordered withBackground className={cx('block')}>
              <HorizontalGroup justify="space-between">
                <HorizontalGroup spacing="md">
                  <Icon name="cog" size="xl" />
                  <VerticalGroup spacing="none">
                    <Text type="primary" size="large">
                      Create schedule by API
                    </Text>
                    <Text type="secondary">Use API or Terraform to manage rotations</Text>
                  </VerticalGroup>
                </HorizontalGroup>
                <a
                  target="_blank"
                  href="https://grafana.com/blog/2022/08/29/get-started-with-grafana-oncall-and-terraform/"
                  rel="noreferrer"
                >
                  <Button variant="secondary">Read more</Button>
                </a>
              </HorizontalGroup>
            </Block>
          </VerticalGroup>
        </div>
      </Drawer>
      {showScheduleForm && (
        <ScheduleForm
          id="new"
          type={type}
          onUpdate={() => {
            onHide();
            onUpdate();
          }}
          onCreate={onCreate}
          onHide={() => {
            setType(undefined);
            setShowScheduleForm(false);
          }}
        />
      )}
    </>
  );
};

export default NewScheduleSelector;
