import dayjs from 'dayjs';

import { getDateForDatePicker } from './RotationForm.helpers';

describe('RotationForm helpers', () => {
  describe('getDateForDatePicker()', () => {
    it(`should return the same regular JS Date as input dayJsDate 
        even if selected day of month doesn't exist in current month
        (in this case there is no 30th Feb and it should still work ok)`, () => {
      jest.useFakeTimers().setSystemTime(new Date('2024-02-01'));

      const inputDate = dayjs()
        .utcOffset(360)
        .set('year', 2024)
        .set('month', 3) // 0-indexed so April
        .set('date', 30)
        .set('hour', 12)
        .set('minute', 20);
      const result = getDateForDatePicker(inputDate);

      expect(result.toString()).toContain('Tue Apr 30 2024');
    });
  });
});
