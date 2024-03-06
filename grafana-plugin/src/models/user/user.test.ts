import { makeRequest as makeRequestOriginal } from 'network/network';
import { RootStore } from 'state/rootStore';

import { UserStore } from './user';
import { UserHelper } from './user.helpers';

const makeRequest = makeRequestOriginal as jest.Mock<ReturnType<typeof makeRequestOriginal>>;

jest.mock('network/network');

afterEach(() => {
  jest.resetAllMocks();
});

describe('UserStore.fetchBackendConfirmationCode', () => {
  const userPk = '5';
  const backend = 'dfkjfdjkfdkjfdaaa';
  const mockedQrCode = 'dfkjfdkjfdkjfdjk';

  test('it makes the proper API call and returns the response', async () => {
    makeRequest.mockResolvedValueOnce(mockedQrCode);

    expect(await UserHelper.fetchBackendConfirmationCode(userPk, backend)).toEqual(mockedQrCode);

    expect(makeRequest).toHaveBeenCalledTimes(1);
    expect(makeRequest).toHaveBeenCalledWith(`/users/${userPk}/get_backend_verification_code?backend=${backend}`, {
      method: 'GET',
    });
  });
});

describe('UserStore.unlinkBackend', () => {
  const rootStore = new RootStore();
  const userStore = new UserStore(rootStore);

  const userPk = '5';
  const backend = 'dfkjfdjkfdkjfdaaa';

  test('it makes the proper API call and returns the response', async () => {
    makeRequest.mockResolvedValueOnce('hello');

    Object.defineProperty(userStore, 'loadCurrentUser', { value: jest.fn() });

    await userStore.unlinkBackend(userPk, backend);

    expect(makeRequest).toHaveBeenCalledTimes(1);
    expect(makeRequest).toHaveBeenCalledWith(`/users/${userPk}/unlink_backend/?backend=${backend}`, {
      method: 'POST',
    });

    expect(userStore.loadCurrentUser).toHaveBeenCalledTimes(1);
    expect(userStore.loadCurrentUser).toHaveBeenCalledWith();
  });
});
