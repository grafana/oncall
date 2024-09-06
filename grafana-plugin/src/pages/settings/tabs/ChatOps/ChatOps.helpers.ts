import { LocationHelper } from 'helpers/LocationHelper';
import { openErrorNotification } from 'helpers/helpers';

export const handleChatOpsQueryParamError = () => {
  const error = LocationHelper.getQueryParam('error');

  if (error) {
    openErrorNotification(error);
    LocationHelper.update({ error: undefined }, 'partial');
  }
};
