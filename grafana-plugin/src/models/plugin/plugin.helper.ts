import { makeRequest } from 'network/network';

export class PluginHelper {
  static async install() {
    return makeRequest(`/plugin/install`, {
      method: 'POST',
    });
  }
}
