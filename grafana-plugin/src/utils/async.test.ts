import { retryFailingPromises } from './async';

describe('retryFailingPromises', () => {
  it('should retry failing promises X times and return correct result', async () => {
    const MAX_ATTEMPTS = 5;

    // We mimic that fetch1 always resolves, fetch2 always rejects and fetch3 resolves only on 2nd attempt
    let attempts1 = 0;
    let attempts2 = 0;
    let attempts3 = 0;
    const fetch1 = async () => Promise.resolve(++attempts1);
    const fetch2 = async () => Promise.reject(++attempts2);
    const fetch3 = async () =>
      new Promise((resolve, reject) => {
        attempts3++;
        if (attempts3 === 2) {
          resolve(attempts3);
        }
        reject(attempts3);
      });

    const result = await retryFailingPromises([fetch1, fetch2, fetch3], { maxAttempts: MAX_ATTEMPTS, delayInMs: 50 });

    expect(attempts1).toBe(1);
    expect(attempts2).toBe(MAX_ATTEMPTS);
    expect(attempts3).toBe(2);
    expect(result).toEqual([
      { status: 'fulfilled', value: 1 },
      { status: 'rejected', reason: 5 },
      { status: 'fulfilled', value: 2 },
    ]);
  });
});
