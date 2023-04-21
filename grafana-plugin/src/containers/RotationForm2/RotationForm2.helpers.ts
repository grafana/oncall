export const getRepeatShiftsEveryOptions = (repeatEveryPeriod: number) => {
  const count = repeatEveryPeriod === 3 ? 24 : 30;
  return Array.from(Array(count + 1).keys())
    .slice(1)
    .map((i) => ({ label: String(i), value: i }));
};
