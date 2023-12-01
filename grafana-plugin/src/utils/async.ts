import { AttemptContext, retry } from '@lifeomic/attempt';

export const retryFailingPromises = async (
  asyncActions: Array<(ctx?: AttemptContext) => Promise<unknown>>,
  { maxAttempts = 3, delayInMs = 500 }: { maxAttempts?: number; delayInMs?: number } = {}
) =>
  maxAttempts === 0
    ? Promise.allSettled(asyncActions)
    : Promise.allSettled(asyncActions.map((asyncAction) => retry(asyncAction, { maxAttempts, delay: delayInMs })));
