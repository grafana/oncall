import { sleep } from 'k6';
import http from 'k6/http';
import { Counter } from 'k6/metrics';

const alerts_number = new Counter('alerts_number');
const alert_groups_number = new Counter('alert_groups_number');

export const ONCALL_INTEGRATION_URL = __ENV.ONCALL_INTEGRATION_URL;
export const TEST_ID = __ENV.TEST_ID;


export function setup() {
  return {
    // Formatted webhook integration
    oncall_integration_url: ONCALL_INTEGRATION_URL,
    test_id: TEST_ID,
    // test_id: Math.random(),
    };
}

// See https://k6.io/docs/using-k6/options
export const options = {
  scenarios: {
    constant_request_rate: {
      executor: 'constant-arrival-rate',
      rate: 1,
      timeUnit: '1s',
      // duration: '1m',
      duration: '10s',
      preAllocatedVUs: 1,
      maxVUs: 1,
    },
  },
}

export default function main(data) {
  alerts_number.add(1);
  alert_groups_number.add(1);
  let res = http.post(
    data.oncall_integration_url,
    JSON.stringify({
      "alert_uid": "08d6891a-835c-e661-39fa-96b6a9e26552" + Math.random(),
      "title": data.test_id,
      "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/ee/Grumpy_Cat_by_Gage_Skidmore.jpg",
      "state": "alerting",
      "link_to_upstream_details": "https://en.wikipedia.org/wiki/Downtime",
      "message": "Smth happened. Oh no!"
    }),
    {
      headers: {
        'content-type': 'application/json',
      },
    });
  sleep(1);
}
