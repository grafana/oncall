import React, { FC } from 'react';

import { IconButton, Stack, useStyles2 } from '@grafana/ui';

import { Avatar } from 'components/Avatar/Avatar';
import { Text } from 'components/Text/Text';
import { getAddRespondersStyles } from 'containers/AddResponders/AddResponders.styles';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';

type Props = {
  team: GrafanaTeam | null;
  handleDelete: React.MouseEventHandler<HTMLButtonElement>;
};

export const TeamResponder: FC<Props> = ({ team: { avatar_url, name }, handleDelete }) => {
  const styles = useStyles2(getAddRespondersStyles);

  return (
    <li>
      <Stack justifyContent="space-between">
        <Stack>
          <div className={styles.timelineIconBackground}>
            <Avatar size="medium" src={avatar_url} />
          </div>
          <Text className={styles.responderName}>{name}</Text>
        </Stack>
        <IconButton
          data-testid="team-responder-delete-icon"
          tooltip="Remove responder"
          name="trash-alt"
          onClick={handleDelete}
        />
      </Stack>
    </li>
  );
};
