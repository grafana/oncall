import React from 'react';

import { Badge, Button, Tooltip } from '@grafana/ui';
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
            <Text type="secondary">(default)</Text>
          </Tooltip>
        )}
      </>
    );
  };

  const renderActionButtons = () => {
    const editButton = (
      <WithPermissionControlTooltip userAction={UserActions.APIKeysWrite}>
        <Button
          fill="text"
          variant="primary"
          onClick={() => {
            // this.setState({ showEditTeamModal: true });
          }}
        >
          Edit
        </Button>
      </WithPermissionControlTooltip>
    );
    return editButton;
  };

  // const renderShowUsersButtons = () => {
  //   const showUsersButton = (
  //     <WithPermissionControlTooltip userAction={UserActions.APIKeysWrite}>
  //       <Icon name="external-link-alt" />
  //     </WithPermissionControlTooltip>
  //   );
  //   return showUsersButton;
  // };

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

  // const { userStore } = store;

  // const user = userStore.items[id];
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
    // {
    //   width: '30%',
    //   title: 'Users',
    //   key: 'action',
    //   render: renderShowUsersButtons,
    // },
    {
      width: '15%',
      key: 'action',
      render: renderActionButtons,
    },
  ];

  return (
    <>
      <GTable
        // emptyText={initialUsersLoaded ? 'No users found' : 'Loading...'}
        rowKey="id"
        data={store.grafanaTeamStore.getSearchResult()}
        columns={columns}
      />

      {/* {showEditTeamModal && (*/}
      {/*  <EditTeamForm*/}
      {/*    visible={showEditTeamModal}*/}
      {/*    onUpdate={this.handleCreateToken}*/}
      {/*    onHide={() => {*/}
      {/*      this.setState({ showEditTeamModal: false });*/}
      {/*    }}*/}
      {/*  />*/}
      {/*)}*/}
    </>
  );
});

export default TeamsList;
