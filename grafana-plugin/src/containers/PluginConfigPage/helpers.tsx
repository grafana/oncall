export const constructSyncErrorMessage = (errMsg: string, url?: string): string => `${url ? `${url}\n` : ''}${errMsg}`;

export const constructErrorActionMessage = (msg?: string): string =>
  `Try removing your current configuration, ${
    msg ? msg : 'double checking your settings'
  }, and re-initializing the plugin.\nBy removing your current configuration, you will need to ensure that you regenerate a new invite token, and input this in your new configuration.`;
