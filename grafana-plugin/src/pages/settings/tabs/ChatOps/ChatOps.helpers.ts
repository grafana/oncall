import { LocationHelper } from 'utils/LocationHelper';
import { openErrorNotification } from 'utils/utils';

export const handleChatOpsQueryParamError = () => {
  const error = LocationHelper.getQueryParam('error');

  if (error) {
    openErrorNotification(error);
    LocationHelper.update({ error: undefined }, 'partial');
  }
};
