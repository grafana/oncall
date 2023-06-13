import React, { useCallback, useState } from 'react';

import { Badge, Button, Field, HorizontalGroup, Modal, RadioButtonList, Tooltip, VerticalGroup } from '@grafana/ui';
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
  const { userStore } = store;

  const isTeamDefault = (record: GrafanaTeam) => {
    return (
      (record.id === 'null' && store.userStore.currentUser?.current_team === null) ||
      record.id === store.userStore.currentUser?.current_team
    );
  };

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
        {isTeamDefault(record) && (
          <>
            {' '}
            <Badge
              text="Default"
              color="green"
              tooltip={
                (record.id === 'null' ? 'No team' : 'This team') +
                ` will be selected by default when creating new resources`
              }
            />
          </>
        )}
      </>
    );
  };

  const renderActionButtons = (record: GrafanaTeam) => {
    const editButton = (
      <HorizontalGroup justify="flex-end">
        <Tooltip content="Default team will be selected when creating new resources">
          <Button
            onClick={async () => {
              await userStore.updateCurrentUser({ current_team: record.id });
              store.grafanaTeamStore.updateItems();
            }}
            disabled={isTeamDefault(record)}
            fill="text"
          >
            Make default
          </Button>
        </Tooltip>
        <WithPermissionControlTooltip userAction={UserActions.TeamsWrite}>
          <Button
            fill="text"
            disabled={record.id === 'null'}
            variant="primary"
            onClick={() => {
              setTeamIdToShowModal(record.id);
            }}
          >
            Edit
          </Button>
        </WithPermissionControlTooltip>
      </HorizontalGroup>
    );
    return editButton;
  };

  const renderPermissions = (record: GrafanaTeam) => {
    return (
      <>
        {record.id === 'null' ? (
          <Text>All users, as no team is assigned to resources</Text>
        ) : (
          <Text>{record.is_sharing_resources_to_all ? 'All users' : 'Only team members and admins'}</Text>
        )}
      </>
    );
  };

  const columns = [
    {
      width: '30%',
      key: 'teamname',
      title: 'Team',
      render: (item: GrafanaTeam) => renderTeam(item),
    },
    {
      width: '65%',
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

  return (
    <>
      <Text type="secondary">
        To manage teams or add users, please visit{' '}
        <a href="/org/teams" target="_blank">
          Grafana teams management
        </a>
      </Text>
      <GTable rowKey="id" data={store.grafanaTeamStore.getSearchResult()} columns={columns} />

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
  const { grafanaTeamStore } = store;
  const team = grafanaTeamStore.items[teamId];

  const [shareResourceToAll, setShareResourceToAll] = useState<string>(
    String(Number(team.is_sharing_resources_to_all))
  );

  const handleSubmit = useCallback(() => {
    Promise.all([
      grafanaTeamStore.updateTeam(teamId, { is_sharing_resources_to_all: Boolean(Number(shareResourceToAll)) }),
    ]).then(onHide);
  }, [shareResourceToAll]);

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
            <div style={{ marginTop: '8px' }}>
              <RadioButtonList
                name="shareResourceToAll"
                options={[
                  { label: 'All Users', value: '1' },
                  { label: 'Team members and admins', value: '0' },
                ]}
                value={shareResourceToAll}
                onChange={setShareResourceToAll}
              />
            </div>
          </Field>
        </VerticalGroup>
      </WithPermissionControlTooltip>

      <HorizontalGroup>
        <Button onClick={onHide} variant="secondary">
          Cancel
        </Button>
        <Button onClick={handleSubmit} variant="primary">
          Save
        </Button>
      </HorizontalGroup>
    </Modal>
  );
};

export default TeamsList;
