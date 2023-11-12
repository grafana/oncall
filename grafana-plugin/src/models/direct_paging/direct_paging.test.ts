import { makeRequest as makeRequestOriginal } from 'network';
import { RootStore } from 'state';

import { DirectPagingStore } from './direct_paging';

const makeRequest = makeRequestOriginal as jest.Mock<ReturnType<typeof makeRequestOriginal>>;

jest.mock('network');

afterEach(() => {
  jest.resetAllMocks();
});

describe('DirectPagingStore', () => {
  const generateStore = () => {
    const rootStore = new RootStore();
    return new DirectPagingStore(rootStore);
  };

  test('addUserToSelectedUsers properly updates the state', async () => {
    const directPagingStore = generateStore();
    const newUser = {
      id: '123',
      username: 'test',
    };

    directPagingStore.addUserToSelectedUsers(newUser as any);

    expect(directPagingStore.selectedUserResponders).toEqual([
      {
        data: newUser,
        important: false,
      },
    ]);
  });

  test('resetSelectedUsers properly resets the state', async () => {
    const directPagingStore = generateStore();
    const newUser = {
      id: '123',
      username: 'test',
    };

    directPagingStore.addUserToSelectedUsers(newUser as any);
    expect(directPagingStore.selectedUserResponders).toHaveLength(1);

    directPagingStore.resetSelectedUsers();
    expect(directPagingStore.selectedUserResponders).toEqual([]);
  });

  test('updateSelectedTeam properly updates the state', async () => {
    const directPagingStore = generateStore();
    const newTeam = {
      id: '123',
    };

    expect(directPagingStore.selectedTeamResponder).toBeNull();
    directPagingStore.updateSelectedTeam(newTeam as any);
    expect(directPagingStore.selectedTeamResponder).toEqual(newTeam);
  });

  test('resetSelectedTeam properly resets the state', async () => {
    const directPagingStore = generateStore();
    const newTeam = {
      id: '123',
    };
    directPagingStore.updateSelectedTeam(newTeam as any);
    expect(directPagingStore.selectedTeamResponder).not.toBeNull();

    directPagingStore.resetSelectedTeam();
    expect(directPagingStore.selectedTeamResponder).toBeNull();
  });

  test('removeSelectedUser properly updates the state', async () => {
    const directPagingStore = generateStore();
    const newUsers = [
      {
        id: '123',
        username: 'test',
      },
      {
        id: '456',
        username: 'test2',
      },
    ] as any;
    directPagingStore.addUserToSelectedUsers(newUsers[0]);
    directPagingStore.addUserToSelectedUsers(newUsers[1]);

    expect(directPagingStore.selectedUserResponders).toHaveLength(2);

    directPagingStore.removeSelectedUser(0);

    expect(directPagingStore.selectedUserResponders).toHaveLength(1);
    expect(directPagingStore.selectedUserResponders[0].data).toEqual(newUsers[1]);
  });

  test('updateSelectedUserImportantStatus properly updates the state', async () => {
    const directPagingStore = generateStore();
    const newUsers = [
      {
        id: '123',
        username: 'test',
      },
      {
        id: '456',
        username: 'test2',
      },
    ] as any;
    directPagingStore.addUserToSelectedUsers(newUsers[0]);
    directPagingStore.addUserToSelectedUsers(newUsers[1]);

    expect(directPagingStore.selectedUserResponders).toHaveLength(2);

    expect(directPagingStore.selectedUserResponders[1].important).toEqual(false);
    directPagingStore.updateSelectedUserImportantStatus(1, true);
    expect(directPagingStore.selectedUserResponders[1].important).toEqual(true);
  });

  test('createManualAlertRule makes the proper API call and returns the response', async () => {
    const directPagingStore = generateStore();
    const mockedRequest = { team: '12345', users: [{ id: 'asdfadf', important: true }] };
    const mockedResponse = { alert_group_id: '123' };

    makeRequest.mockResolvedValueOnce(mockedResponse);

    expect(await directPagingStore.createManualAlertRule(mockedRequest)).toEqual(mockedResponse);

    expect(makeRequest).toHaveBeenCalledTimes(1);
    expect(makeRequest).toHaveBeenCalledWith('/direct_paging/', {
      method: 'POST',
      data: mockedRequest,
    });
  });

  test('updateAlertGroup makes the proper API call and returns the response', async () => {
    const directPagingStore = generateStore();
    const alertGroupId = '134';
    const mockedRequest = { team: '12345', users: [{ id: 'asdfadf', important: true }] };
    const mockedResponse = { alert_group_id: alertGroupId };

    makeRequest.mockResolvedValueOnce(mockedResponse);

    expect(await directPagingStore.updateAlertGroup(alertGroupId, mockedRequest)).toEqual(mockedResponse);

    expect(makeRequest).toHaveBeenCalledTimes(1);
    expect(makeRequest).toHaveBeenCalledWith('/direct_paging/', {
      method: 'POST',
      data: {
        alert_group_id: alertGroupId,
        ...mockedRequest,
      },
    });
  });
});
