import { makeRequest as makeRequestOriginal } from 'network';
import { RootStore } from 'state';

import { UserStore } from './user';

const makeRequest = makeRequestOriginal as jest.Mock<ReturnType<typeof makeRequestOriginal>>;

jest.mock('network');

afterEach(() => {
  jest.resetAllMocks();
});

describe('UserStore.sendBackendConfirmationCode', () => {
  const rootStore = new RootStore();
  const userStore = new UserStore(rootStore);

  const userPk = '5';
  const backend = 'dfkjfdjkfdkjfdaaa';
  const mockedQrCode = 'dfkjfdkjfdkjfdjk';

  test('it makes the proper API call and returns the response', async () => {
    makeRequest.mockResolvedValueOnce(mockedQrCode);

    expect(await userStore.sendBackendConfirmationCode(userPk, backend)).toEqual(mockedQrCode);

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

    userStore.loadCurrentUser = jest.fn();

    await userStore.unlinkBackend(userPk, backend);

    expect(makeRequest).toHaveBeenCalledTimes(1);
    expect(makeRequest).toHaveBeenCalledWith(`/users/${userPk}/unlink_backend/?backend=${backend}`, {
      method: 'POST',
    });

    expect(userStore.loadCurrentUser).toHaveBeenCalledTimes(1);
    expect(userStore.loadCurrentUser).toHaveBeenCalledWith();
  });
});
