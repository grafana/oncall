import React, { useState, FC, createContext, PropsWithChildren, useCallback } from 'react';

import { SelectableValue } from '@grafana/data';

import { ResponderType, UserResponders } from 'containers/AddResponders/AddResponders.types';
import { GrafanaTeam } from 'models/grafana_team/grafana_team.types';
import { User } from 'models/user/user.types';

type DirectPagingContextDefault = {
  selectedTeamResponder: GrafanaTeam | null;
  selectedUserResponders: UserResponders;
  addUserToSelectedUsers: (user: User) => void;
  resetSelectedUsers: () => void;
  updateSelectedTeam: (team: GrafanaTeam) => void;
  resetSelectedTeam: () => void;
  generateRemoveSelectedUserHandler: (index: number) => () => void;
  generateUpdateSelectedUserImportantStatusHandler: (index: number) => (value: SelectableValue<number>) => void;
};

export const DirectPagingContext = createContext<DirectPagingContextDefault>({
  selectedTeamResponder: null,
  selectedUserResponders: [],
  addUserToSelectedUsers: () => {},
  resetSelectedUsers: () => {},
  updateSelectedTeam: () => {},
  resetSelectedTeam: () => {},
  generateRemoveSelectedUserHandler: () => () => {},
  generateUpdateSelectedUserImportantStatusHandler: () => () => {},
});

export const DirectPagingProvider: FC<PropsWithChildren> = ({ children }) => {
  const [selectedTeamResponder, setSelectedTeamResponder] = useState<GrafanaTeam>(null);
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

  const resetSelectedUsers = useCallback(() => {
    setSelectedUserResponders([]);
  }, [setSelectedUserResponders]);

  const resetSelectedTeam = useCallback(() => {
    setSelectedTeamResponder(null);
  }, [setSelectedTeamResponder]);

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
        resetSelectedUsers,
        updateSelectedTeam: setSelectedTeamResponder,
        resetSelectedTeam,
        generateRemoveSelectedUserHandler,
        generateUpdateSelectedUserImportantStatusHandler,
      }}
    >
      {children}
    </DirectPagingContext.Provider>
  );
};
