import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { Heartbeat } from 'models/heartbeat/heartbeat.types';
import { makeRequest as makeRequestOriginal } from 'network';
import { RootStore } from 'state';
import { PageNumberPaginatedApiResponse } from 'utils/pagination/types';

import { AlertReceiveChannelIdToObjectMap, AlertReceiveChannelStore } from './alert_receive_channel';
import { AlertReceiveChannel, AlertReceiveChannelOption } from './alert_receive_channel.types';

const makeRequest = makeRequestOriginal as jest.Mock<ReturnType<typeof makeRequestOriginal>>;

jest.mock('network');

afterEach(() => {
  jest.resetAllMocks();
});

const createIntegration = (id: string, verbal_name: string): AlertReceiveChannel =>
  ({ id, verbal_name } as AlertReceiveChannel);

const createHeartbeat = (id: string, alert_receive_channel: string): Heartbeat =>
  ({ id, alert_receive_channel } as Heartbeat);

const createChannelFilter = (id: string, alert_receive_channel: string): ChannelFilter =>
  ({ id, alert_receive_channel } as ChannelFilter);

const createAlertReceiveChannelOption = (display_name: string, value: number): AlertReceiveChannelOption =>
  ({ display_name, value } as AlertReceiveChannelOption);

const createPaginatedSearchResults = <RT>(results: RT[]): PageNumberPaginatedApiResponse<RT> => ({
  results,
  next: 'asdfasdf',
  previous: 'cnmcvmnvc',
  page_size: 1,
  count: 2,
  current_page_number: 1,
  total_pages: 2,
});

describe('AlertReceiveChannelStore', () => {
  const rootStore = new RootStore();

  const integration1 = createIntegration('test1', '1');
  const integration2 = createIntegration('test2', '2');
  const integration3 = createIntegration('test3', '3');

  const heartbeat1 = createHeartbeat('heartbeat1', integration1.id);
  const channelFilter1 = createChannelFilter('cf1', integration1.id);

  const items: AlertReceiveChannelIdToObjectMap = {
    [integration1.id]: integration1,
    [integration2.id]: integration2,
    [integration3.id]: integration3,
  };

  const heartbeatStoreItems = {
    [heartbeat1.id]: heartbeat1,
  };

  const channelFilters = {
    [channelFilter1.id]: channelFilter1,
  };
  const channelFilterIds = {
    [integration1.id]: [channelFilter1.id],
  };

  const integration4 = createIntegration('test4', '4');
  // const heartbeat2 = createHeartbeat('heartbeat2', integration4.id);
  const channelFilter2 = createChannelFilter('cf2', integration4.id);

  const createAlertReceiveChannelStore = () => {
    const alertReceiveChannelStore = new AlertReceiveChannelStore(rootStore);
    alertReceiveChannelStore.items = items;
    return alertReceiveChannelStore;
  };

  test('getSearchResult', () => {
    const alertReceiveChannelStore = createAlertReceiveChannelStore();

    alertReceiveChannelStore.searchResult = undefined;
    expect(alertReceiveChannelStore.getSearchResult()).toEqual(undefined);

    alertReceiveChannelStore.searchResult = [];
    expect(alertReceiveChannelStore.getSearchResult()).toEqual([]);

    alertReceiveChannelStore.searchResult = [integration1.id, integration2.id, integration3.id];
    expect(alertReceiveChannelStore.getSearchResult()).toEqual([integration1, integration2, integration3]);
  });

  test('getPaginatedSearchResult', () => {
    const alertReceiveChannelStore = createAlertReceiveChannelStore();

    alertReceiveChannelStore.paginatedSearchResult = null;
    expect(alertReceiveChannelStore.getPaginatedSearchResult()).toEqual(undefined);

    alertReceiveChannelStore.paginatedSearchResult = createPaginatedSearchResults([
      integration1.id,
      integration2.id,
      integration3.id,
    ]);
    expect(alertReceiveChannelStore.getPaginatedSearchResult()).toEqual(
      createPaginatedSearchResults([integration1, integration2, integration3])
    );
  });

  test.each([null, integration1])('loadItem - item = %s', async (response) => {
    const id = '5';
    const alertReceiveChannelStore = createAlertReceiveChannelStore();
    const getByIdSpy = jest
      .spyOn(alertReceiveChannelStore, 'getById')
      .mockImplementation(() => Promise.resolve(response));

    const expected = response ? integration1 : undefined;

    expect(await alertReceiveChannelStore.loadItem(id)).toEqual(expected);
    expect(getByIdSpy).toHaveBeenCalledTimes(1);
    expect(getByIdSpy).toHaveBeenCalledWith(id, false);

    const expectedItems = alertReceiveChannelStore.items;
    if (response) {
      expectedItems[id] = response;
    }

    expect(alertReceiveChannelStore.items).toEqual(expectedItems);
  });

  test('updateItems', async () => {
    const alertReceiveChannelStore = createAlertReceiveChannelStore();
    rootStore.heartbeatStore.items = heartbeatStoreItems;

    const updateCountersSpy = jest
      .spyOn(alertReceiveChannelStore, 'updateCounters')
      .mockImplementation(() => Promise.resolve());

    const results = [integration4];
    const paginatedResult = createPaginatedSearchResults(results);
    const { id } = integration4;

    makeRequest.mockResolvedValue(paginatedResult);

    const filters = 'hello';
    const page = 5;

    const updateItemsResponse = await alertReceiveChannelStore.updateItems(filters, page);

    expect(updateItemsResponse).toEqual(results);
    expect(makeRequest).toHaveBeenCalledTimes(1);
    expect(makeRequest).toHaveBeenCalledWith('/alert_receive_channels/', {
      params: { search: filters, page },
    });

    expect(alertReceiveChannelStore.items).toEqual({
      ...alertReceiveChannelStore.items,
      [id]: integration4,
    });
    expect(alertReceiveChannelStore.searchResult).toEqual([id]);
    expect(alertReceiveChannelStore.paginatedSearchResult).toEqual({
      ...paginatedResult,
      results: [id],
    });

    // TODO: may be able to remove the following two assertions
    // expect(alertReceiveChannelStore.rootStore.heartbeatStore.items).toEqual({
    //   ...alertReceiveChannelStore.rootStore.heartbeatStore.items,
    //   [heartbeat2.id]: heartbeat2,
    // });
    // expect(alertReceiveChannelStore.alertReceiveChannelToHeartbeat).toEqual({
    //   ...alertReceiveChannelStore.alertReceiveChannelToHeartbeat,
    //   [integration4.id]: heartbeat2.id,
    // });

    expect(updateCountersSpy).toHaveBeenCalledTimes(1);
    expect(updateCountersSpy).toHaveBeenCalledWith();

    const multipleFilters = { foo: 'bar', abc: '123' };

    await alertReceiveChannelStore.updateItems(multipleFilters);
    expect(makeRequest).toHaveBeenCalledWith('/alert_receive_channels/', {
      params: { ...multipleFilters, page: 1 },
    });
  });

  test.each([true, false])('updateChannelFilters - isOverwrite: %s', async (isOverwrite) => {
    const alertReceiveChannelStore = createAlertReceiveChannelStore();
    alertReceiveChannelStore.channelFilters = channelFilters;
    alertReceiveChannelStore.channelFilterIds = channelFilterIds;

    const { id, alert_receive_channel } = channelFilter2;

    makeRequest.mockResolvedValue([channelFilter2]);

    await alertReceiveChannelStore.updateChannelFilters(alert_receive_channel, isOverwrite);
    expect(makeRequest).toHaveBeenCalledTimes(1);
    expect(makeRequest).toHaveBeenCalledWith(alertReceiveChannelStore.channelFiltersPath, {
      params: { alert_receive_channel },
    });

    expect(alertReceiveChannelStore.channelFilters).toEqual({
      ...(isOverwrite ? {} : alertReceiveChannelStore.channelFilters),
      [id]: channelFilter2,
    });

    expect(alertReceiveChannelStore.channelFilterIds).toEqual({
      ...alertReceiveChannelStore.channelFilterIds,
      [alert_receive_channel]: [id],
    });
  });

  test('updateChannelFilter', async () => {
    const alertReceiveChannelStore = createAlertReceiveChannelStore();
    const { id } = channelFilter2;

    makeRequest.mockResolvedValue(channelFilter2);

    await alertReceiveChannelStore.updateChannelFilter(id);
    expect(makeRequest).toHaveBeenCalledTimes(1);
    expect(makeRequest).toHaveBeenCalledWith(`${alertReceiveChannelStore.channelFiltersPath}${id}/`);

    expect(alertReceiveChannelStore.channelFilters).toEqual({
      ...alertReceiveChannelStore.channelFilters,
      [id]: channelFilter2,
    });
  });

  test('createChannelFilter', async () => {
    const alertReceiveChannelStore = createAlertReceiveChannelStore();
    const newChannelFilter = createChannelFilter('5', integration3.id);

    makeRequest.mockResolvedValue(newChannelFilter);

    expect(await alertReceiveChannelStore.createChannelFilter(newChannelFilter)).toEqual(newChannelFilter);
    expect(makeRequest).toHaveBeenCalledTimes(1);
    expect(makeRequest).toHaveBeenCalledWith(alertReceiveChannelStore.channelFiltersPath, {
      method: 'POST',
      data: newChannelFilter,
    });
  });

  // test('moveChannelFilterToPosition', async () => {
  //   const alertReceiveChannelStore = createAlertReceiveChannelStore();
  //   const channelFilterChanges = { ...channelFilter2, slack_channel_id: 'asdfasdf' };

  //   makeRequest.mockResolvedValue(channelFilterChanges);

  //   expect(await alertReceiveChannelStore.saveChannelFilter(channelFilter2.id, channelFilterChanges)).toEqual(
  //     channelFilterChanges
  //   );
  //   expect(makeRequest).toHaveBeenCalledTimes(1);
  //   expect(makeRequest).toHaveBeenCalledWith(`${alertReceiveChannelStore.channelFiltersPath}${channelFilter2.id}/`, {
  //     method: 'PUT',
  //     data: channelFilterChanges,
  //   });

  //   expect(alertReceiveChannelStore.channelFilters).toEqual({
  //     ...alertReceiveChannelStore.channelFilters,
  //     [channelFilter2.id]: channelFilterChanges,
  //   });
  // });

  test('deleteChannelFilter', async () => {
    const alertReceiveChannelStore = createAlertReceiveChannelStore();
    alertReceiveChannelStore.channelFilters = channelFilters;
    alertReceiveChannelStore.channelFilterIds = channelFilterIds;

    const { id, alert_receive_channel } = channelFilters[channelFilter1.id];

    const updateChannelFiltersSpy = jest
      .spyOn(alertReceiveChannelStore, 'updateChannelFilters')
      .mockImplementation(() => Promise.resolve());

    makeRequest.mockResolvedValue(null);

    await alertReceiveChannelStore.deleteChannelFilter(id);

    expect(makeRequest).toHaveBeenCalledTimes(1);
    expect(makeRequest).toHaveBeenCalledWith(`${alertReceiveChannelStore.channelFiltersPath}${id}`, {
      method: 'DELETE',
    });

    expect(alertReceiveChannelStore.channelFilterIds).toEqual({
      [alert_receive_channel]: [],
    });

    expect(updateChannelFiltersSpy).toHaveBeenCalledTimes(1);
    expect(updateChannelFiltersSpy).toHaveBeenCalledWith(alert_receive_channel, true);
  });

  test('updateAlertReceiveChannelOptions', async () => {
    const alertReceiveChannelStore = createAlertReceiveChannelStore();
    const results = [createAlertReceiveChannelOption('arco1', 1), createAlertReceiveChannelOption('arco2', 2)];

    makeRequest.mockResolvedValue(results);

    await alertReceiveChannelStore.updateAlertReceiveChannelOptions();

    expect(makeRequest).toHaveBeenCalledTimes(1);
    expect(makeRequest).toHaveBeenCalledWith('/alert_receive_channels/integration_options/');
    expect(alertReceiveChannelStore.alertReceiveChannelOptions).toEqual(results);
  });
});
