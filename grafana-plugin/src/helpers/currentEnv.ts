//@ts-ignore
import plugin from '../../package.json'; // eslint-disable-line

const CLOUD_VERSION_REGEX = /^(v\d+\.\d+\.\d+|grafana-(irm|oncall)-app-v\d+\.\d+\.\d+(-\d+.*)?)$/;

export const determineCurrentEnv = (): 'oss' | 'cloud' | 'local' => {
  if (CLOUD_VERSION_REGEX.test(plugin?.version)) {
    return 'cloud';
  }
  try {
    return process.env.NODE_ENV === 'development' ? 'local' : 'oss';
  } catch (error) {
    return 'cloud';
  }
};
