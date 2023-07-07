import { action, observable } from 'mobx';

import BaseStore from 'models/base_store';
import { makeRequest } from 'network';
import { RootStore } from 'state';
import { PageNumberPaginatedApiResponse } from 'utils/pagination/types';

import { CloudUser } from './cloud.types';

type CloudUserId = CloudUser['id'];

type CloudUserIdToCloudUserMap = Record<CloudUserId, CloudUser>;
type CloudConnectionStatus = {
  cloud_connection_status: boolean;
  cloud_notifications_enabled: boolean;
  cloud_heartbeat_enabled: boolean;
  cloud_heartbeat_link: string | null;
};

type PaginatedAPIResponse = PageNumberPaginatedApiResponse<CloudUser>;

type CloudUserSyncAPISuccessResponse = {
  status: boolean;
  error: string | null;
};

type CloudUserSyncAPIErrorResponse = {
  detail: string;
};

type CloudUserSyncAPIResponse = CloudUserSyncAPISuccessResponse | CloudUserSyncAPIErrorResponse;

type CloudHeartbeatAPISuccessResponse = {
  link: string | null;
};

type CloudHeartbeatAPIErrorResponse = {
  detail: string;
};

type CloudHeartbeatAPIResponse = CloudHeartbeatAPISuccessResponse | CloudHeartbeatAPIErrorResponse;

export class CloudStore extends BaseStore {
  @observable.shallow
  searchResult: PageNumberPaginatedApiResponse<CloudUserId> = null;

  @observable.shallow
  items: CloudUserIdToCloudUserMap = {};

  @observable
  cloudConnectionStatus: CloudConnectionStatus = { cloud_connection_status: false } as CloudConnectionStatus;

  cloudConnectionPath = '/cloud_connection/';

  constructor(rootStore: RootStore) {
    super(rootStore);

    this.path = '/cloud_users/';
  }

  @action
  async updateItems(page = 1): Promise<void> {
    const { results, ...pagination } = await makeRequest<PaginatedAPIResponse>(this.path, {
      params: { page },
    });

    this.items = {
      ...this.items,
      ...results.reduce(
        (acc, item) => ({
          ...acc,
          [item.id]: item,
        }),
        {} as CloudUserIdToCloudUserMap
      ),
    };

    this.searchResult = {
      ...pagination,
      results: results.map(({ id }) => id),
    };
  }

  getSearchResult(): PaginatedAPIResponse | void {
    const { searchResult } = this;

    if (!searchResult) {
      return;
    }

    return {
      ...searchResult,
      results: searchResult.results.map((id) => this.items[id]),
    };
  }

  syncCloudUsers = (): Promise<CloudUserSyncAPIResponse> =>
    makeRequest<CloudUserSyncAPIResponse>(this.path, { method: 'POST' });

  syncCloudUser = (id: string): Promise<CloudUserSyncAPIResponse> =>
    makeRequest<CloudUserSyncAPIResponse>(`${this.path}${id}/sync/`, { method: 'POST' });

  getCloudHeartbeat = (): Promise<CloudHeartbeatAPIResponse> =>
    makeRequest<CloudHeartbeatAPIResponse>('/cloud_heartbeat/', { method: 'POST' });

  getCloudUser = (id: string): Promise<CloudUser> => makeRequest<CloudUser>(`${this.path}${id}`, { method: 'GET' });

  @action
  async loadCloudConnectionStatus(): Promise<void> {
    this.cloudConnectionStatus = await makeRequest<CloudConnectionStatus>(this.cloudConnectionPath, { method: 'GET' });
  }

  disconnectToCloud = (): Promise<void> => makeRequest<null>(this.cloudConnectionPath, { method: 'DELETE' });
}
