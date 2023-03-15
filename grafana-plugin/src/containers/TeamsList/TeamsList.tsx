import React, { ChangeEvent, useCallback, useState } from 'react';

import {
  Badge,
  Button,
  Checkbox,
  Field,
  HorizontalGroup,
  Modal,
  RadioButtonGroup,
  Tooltip,
  VerticalGroup,
} from '@grafana/ui';
import { observer } from 'mobx-react';

import Avatar from 'components/Avatar/Avatar';
import GTable from 'components/GTable/GTable';
import Text from 'components/Text/Text';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';

const TeamsList = observer(() => {
  const store = useStore();
  const [teamIdToShowModal, setTeamIdToShowModal] = useState<GrafanaTeam['id']>();

  const renderTeam = (record: GrafanaTeam) => {
    return (
      <>
        {record.id === 'null' ? (
          <Badge text={record.name} color={'blue'} tooltip={'Resource is not assigned to any team (ex General team)'} />
        ) : (
          <Text>
            <Avatar size="small" src={record.avatar_url} /> {record.name}{' '}
          </Text>
        )}
        {record.id === store.userStore.currentUser?.current_team && (
          <Tooltip
            content={
              'This team will be selected by default when creating new resources (Integrations, Escalation Chains, Schedules, Outgoing Webhooks)'
            }
          >
            <Tooltip content={'This team will be selected by default when you create new resources'}>
              <Text type="secondary">(default)</Text>
            </Tooltip>
          </Tooltip>
        )}
      </>
    );
  };

  const renderActionButtons = (item: GrafanaTeam) => {
    const editButton = (
      <WithPermissionControlTooltip userAction={UserActions.APIKeysWrite}>
        <Button
          fill="text"
          variant="primary"
          onClick={() => {
            setTeamIdToShowModal(item.id);
          }}
        >
          Edit
        </Button>
      </WithPermissionControlTooltip>
    );
    return editButton;
  };

  const renderPermissions = (record: GrafanaTeam) => {
    return (
      <>
        {record.id === 'null' ? (
          <Text>All users, because no team is assigned</Text>
        ) : (
          <Text>{record.is_sharing_resources_to_all ? 'All users' : 'Only team members and admins'}</Text>
        )}
      </>
    );
  };

  const columns = [
    {
      width: '20%',
      key: 'teamname',
      title: 'Team',
      render: (item: GrafanaTeam) => renderTeam(item),
    },
    {
      width: '75%',
      title: 'Who can see the team name and access the team resources',
      key: 'permissions',
      render: (item: GrafanaTeam) => renderPermissions(item),
    },
    {
      width: '15%',
      key: 'action',
      render: renderActionButtons,
    },
  ];

  //   const onUpdateClickCallback = useCallback(() => {
  //   (store.grafanaTeamStore.saveTeam(id, {
  //
  //       })
  //   )
  //     .then((channelFilter: ChannelFilter) => {
  //       onUpdate(channelFilter.id);
  //       onHide();
  //     })
  //     .catch((err) => {
  //       const errors = get(err, 'response.data');
  //       setErrors(errors);
  //       if (errors?.non_field_errors) {
  //         openErrorNotification(errors.non_field_errors);
  //       }
  //     });
  // }, [filteringTerm, filteringTermType]);

  return (
    <>
      <GTable
        // emptyText={initialUsersLoaded ? 'No users found' : 'Loading...'}
        rowKey="id"
        data={store.grafanaTeamStore.getSearchResult()}
        columns={columns}
      />

      {teamIdToShowModal && (
        <TeamModal
          teamId={teamIdToShowModal}
          onHide={() => {
            setTeamIdToShowModal(undefined);
          }}
        />
      )}
    </>
  );
});

interface TeamModalProps {
  teamId: GrafanaTeam['id'];
  onHide: () => void;
}

const TeamModal = ({ teamId, onHide }: TeamModalProps) => {
  const store = useStore();
  const { grafanaTeamStore, userStore } = store;
  const team = grafanaTeamStore.items[teamId];
  const user = userStore.currentUser;

  const [shareResourceToAll, setShareResourceToAll] = useState<boolean>(team.is_sharing_resources_to_all);
  const [isDefault, setIsDefault] = useState<boolean>(user.current_team === team.id);

  const handleSubmit = useCallback(() => {
    Promise.all([
      grafanaTeamStore.updateTeam(teamId, { is_sharing_resources_to_all: shareResourceToAll }),
      userStore.updateCurrentUser({ current_team: teamId }),
    ]).then(onHide);
  }, [isDefault, shareResourceToAll]);

  return (
    <Modal
      isOpen
      title={
        <HorizontalGroup>
          <Text.Title level={4}>{team.name} settings</Text.Title>
        </HorizontalGroup>
      }
      onDismiss={onHide}
    >
      <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
        <VerticalGroup>
          <Field label="Who can see the team name and access the team resources">
            <RadioButtonGroup
              options={[
                { label: 'All Users', value: true },
                { label: 'Team members and admins', value: false },
              ]}
              value={shareResourceToAll}
              onChange={setShareResourceToAll}
            />
          </Field>
          <Field>
            <Checkbox
              value={isDefault}
              onChange={(event: ChangeEvent<HTMLInputElement>) => {
                setIsDefault(event.target.checked);
              }}
              label="Mark as default team"
              description="This team will be selected by default when you create new resources"
            />
          </Field>
        </VerticalGroup>
      </WithPermissionControlTooltip>

      <HorizontalGroup>
        <Button onClick={onHide} variant="secondary">
          Cancel
        </Button>
        <Button onClick={handleSubmit} variant="primary">
          Submit
        </Button>
      </HorizontalGroup>
    </Modal>
  );
};

export default TeamsList;
