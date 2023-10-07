import React, { useState, FC, createContext, PropsWithChildren, useCallback } from 'react';

import { SelectableValue } from '@grafana/data';

import { ResponderType, TeamResponder, UserResponders } from 'containers/EscalationVariants/EscalationVariants.types';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { User } from 'models/user/user.types';

type DirectPagingContextDefault = {
  selectedTeamResponder: TeamResponder;
  selectedUserResponders: UserResponders;
  addUserToSelectedUsers: (user: User) => void;
  updateSelectedTeam: (team: GrafanaTeam) => void;
  updateSelectedTeamImportantStatus: (value: SelectableValue<number>) => void;
  generateRemoveSelectedUserHandler: (index: number) => () => void;
  generateUpdateSelectedUserImportantStatusHandler: (index: number) => (value: SelectableValue<number>) => void;
};

export const DirectPagingContext = createContext<DirectPagingContextDefault>({
  selectedTeamResponder: undefined,
  selectedUserResponders: [],
  addUserToSelectedUsers: () => {},
  updateSelectedTeam: () => {},
  updateSelectedTeamImportantStatus: () => {},
  generateRemoveSelectedUserHandler: () => () => {},
  generateUpdateSelectedUserImportantStatusHandler: () => () => {},
});

export const DirectPagingProvider: FC<PropsWithChildren> = ({ children }) => {
  const [selectedTeamResponder, setSelectedTeamResponder] = useState<TeamResponder>(null);
  const [selectedUserResponders, setSelectedUserResponders] = useState<UserResponders>([]);

  const addUserToSelectedUsers = useCallback(
    (user: User) => {
      setSelectedUserResponders((users) => [
        ...users,
        {
          type: ResponderType.User,
          data: user,
          important: false,
        },
      ]);
    },
    [setSelectedUserResponders]
  );

  const updateSelectedTeam = useCallback(
    (team: GrafanaTeam | undefined) => {
      setSelectedTeamResponder(
        team === undefined
          ? undefined
          : {
              type: ResponderType.Team,
              data: team,
              important: false,
            }
      );
    },
    [setSelectedTeamResponder]
  );

  const updateSelectedTeamImportantStatus = useCallback(
    ({ value: important }: SelectableValue<number>) => {
      setSelectedTeamResponder({
        ...selectedTeamResponder,
        important: Boolean(important),
      });
    },
    [setSelectedTeamResponder, selectedTeamResponder]
  );

  const generateRemoveSelectedUserHandler = useCallback(
    (index: number) => {
      return () => {
        setSelectedUserResponders((selectedUsers) => [
          ...selectedUsers.slice(0, index),
          ...selectedUsers.slice(index + 1),
        ]);
      };
    },
    [setSelectedUserResponders]
  );

  const generateUpdateSelectedUserImportantStatusHandler = useCallback(
    (index: number) => {
      return ({ value: important }: SelectableValue<number>) => {
        setSelectedUserResponders((selectedUsers) => [
          ...selectedUsers.slice(0, index),
          {
            ...selectedUsers[index],
            important: Boolean(important),
          },
          ...selectedUsers.slice(index + 1),
        ]);
      };
    },
    [setSelectedUserResponders]
  );

  return (
    <DirectPagingContext.Provider
      value={{
        selectedTeamResponder,
        selectedUserResponders,
        addUserToSelectedUsers,
        updateSelectedTeam,
        updateSelectedTeamImportantStatus,
        generateRemoveSelectedUserHandler,
        generateUpdateSelectedUserImportantStatusHandler,
      }}
    >
      {children}
    </DirectPagingContext.Provider>
  );
};
