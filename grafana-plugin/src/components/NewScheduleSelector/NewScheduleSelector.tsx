import React, { FC, useCallback, useState } from 'react';

import { css } from '@emotion/css';
import { Button, Drawer, Icon, Stack, useStyles2 } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { StackSize } from 'helpers/consts';

import { Block } from 'components/GBlock/Block';
import { Text } from 'components/Text/Text';
import { ScheduleForm } from 'containers/ScheduleForm/ScheduleForm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { Schedule, ScheduleType } from 'models/schedule/schedule.types';

interface NewScheduleSelectorProps {
  onHide: () => void;
  onCreate: (data: Schedule) => void;
}

export const NewScheduleSelector: FC<NewScheduleSelectorProps> = ({ onHide, onCreate }) => {
  const [showScheduleForm, setShowScheduleForm] = useState<boolean>(false);
  const [type, setType] = useState<ScheduleType | undefined>();
  const styles = useStyles2(getStyles);

  const getCreateScheduleClickHandler = useCallback((type: ScheduleType) => {
    return () => {
      setType(type);
      setShowScheduleForm(true);
    };
  }, []);

  if (showScheduleForm) {
    return <ScheduleForm id="new" type={type} onSubmit={onCreate} onHide={onHide} />;
  }

  return (
    <Drawer scrollableContent title="Create new schedule" onClose={onHide} closeOnMaskClick={false}>
      <div className={styles.content}>
        <Stack direction="column" gap={StackSize.lg}>
          <Block bordered withBackground className={styles.block}>
            <Stack justifyContent="space-between">
              <Stack gap={StackSize.md}>
                <Icon name="calendar-alt" size="xl" />
                <Stack direction="column" gap={StackSize.none}>
                  <Text type="primary" size="large">
                    Set up on-call rotation schedule
                  </Text>
                  <Text type="secondary">Configure rotations and shifts directly in Grafana On-Call</Text>
                </Stack>
              </Stack>
              <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                <Button variant="primary" icon="plus" onClick={getCreateScheduleClickHandler(ScheduleType.API)}>
                  Create
                </Button>
              </WithPermissionControlTooltip>
            </Stack>
          </Block>
          <Block bordered withBackground className={styles.block}>
            <Stack justifyContent="space-between">
              <Stack gap={StackSize.md}>
                <Icon name="download-alt" size="xl" />
                <Stack direction="column" gap={StackSize.none}>
                  <Text type="primary" size="large">
                    Import schedule from iCal Url
                  </Text>
                  <Text type="secondary">Import rotations and shifts from your calendar app</Text>
                </Stack>
              </Stack>
              <Button variant="secondary" icon="plus" onClick={getCreateScheduleClickHandler(ScheduleType.Ical)}>
                Create
              </Button>
            </Stack>
          </Block>
          <Block bordered withBackground className={styles.block}>
            <Stack justifyContent="space-between">
              <Stack gap={StackSize.md}>
                <Icon name="cog" size="xl" />
                <Stack direction="column" gap={StackSize.none}>
                  <Text type="primary" size="large">
                    Create schedule by API
                  </Text>
                  <Text type="secondary">Use API or Terraform to manage rotations</Text>
                </Stack>
              </Stack>
              <a
                target="_blank"
                href="https://grafana.com/blog/2022/08/29/get-started-with-grafana-oncall-and-terraform/"
                rel="noreferrer"
              >
                <Button variant="secondary">Read more</Button>
              </a>
            </Stack>
          </Block>
        </Stack>
      </div>
    </Drawer>
  );
};

export const getStyles = () => {
  return {
    root: css`
      display: block;
    `,

    block: css`
      width: 100%;
    `,

    content: css`
      padding-bottom: 24px;
    `,
  };
};
