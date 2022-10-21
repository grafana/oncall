import Cookies from 'js-cookie';
import qs from 'query-string';

const query = qs.parse(window.location.search);

if (query.version === 'nf') {
  Cookies.set('nf', '1', { expires: 31, path: '/' });
}

export const getABTestVariant = () => Cookies.get('ab_test_variant');

export const getIsNoFreeExperiment = () => Cookies.get('nf') === '1';
