import React, { useState } from 'react';

import {
  Badge,
  Button,
  Checkbox,
  Field,
  HorizontalGroup,
  Icon,
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
  const [showEditTeamModal, setShowEditTeamModal] = useState(false);

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

  const renderActionButtons = () => {
    const editButton = (
      <WithPermissionControlTooltip userAction={UserActions.APIKeysWrite}>
        <Button
          fill="text"
          variant="primary"
          onClick={() => {
            setShowEditTeamModal(true);
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

      {showEditTeamModal && (
        <Modal
          isOpen
          title={
            <HorizontalGroup>
              <Icon size="lg" name="link" />
              <Text.Title level={4}>Team settings</Text.Title>
            </HorizontalGroup>
          }
          onDismiss={() => {}}
        >
          <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
            <VerticalGroup>
              <Field label="Who can see the team name and access the team resources">
                <RadioButtonGroup
                  options={[
                    { label: 'All Users', value: '123' },
                    { label: 'Team members and admins', value: '456' },
                  ]}
                  value={'123'}
                  onChange={() => {
                    // setErrors({});
                    // setFilteringTermType(value);
                    // setFilteringTerm(renderFilteringTermValue(value));
                  }}
                />
              </Field>
              <Field>
                <Checkbox
                  value={false}
                  onChange={() => {}}
                  label={'Mark as default team'}
                  description={'This team will be selected by default when you create new resources'}
                />
              </Field>
            </VerticalGroup>
          </WithPermissionControlTooltip>

          <HorizontalGroup>
            <Button onClick={() => {}} variant="secondary">
              Cancel
            </Button>
            <Button onClick={() => {}} variant="primary">
              Submit
            </Button>
          </HorizontalGroup>
        </Modal>
      )}
    </>
  );
});

export default TeamsList;
