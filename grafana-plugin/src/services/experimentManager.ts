import Cookies from 'js-cookie';
import qs from 'query-string';

const query = qs.parse(window.location.search);

if (query.version === 'nf') {
  Cookies.set('nf', '1', { expires: 31, path: '/' });
}

export function getABTestVariant() {
  return Cookies.get('ab_test_variant');
}

export function getIsNoFreeExperiment() {
  return Cookies.get('nf') === '1';
}
