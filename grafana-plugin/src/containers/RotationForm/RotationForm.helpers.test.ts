import dayjs, { Dayjs } from 'dayjs';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';

import { dayJSAddWithDSTFixed } from './RotationForm.helpers';

dayjs.extend(timezone);
dayjs.extend(utc);

describe('RotationForm helpers', () => {
  describe('dayJSAddWithDSTFixed() @london-tz', () => {
    it(`corrects resulting hour to be the same as in input if start date is before London DST (GMT + 0) 
      and resulting date is within London DST (GMT + 1)`, () => {
      // Base date is out of DST: 20th Mar 3:00 (GMT + 0)
      const baseDate = dayjs('2018-03-20 3:00');

      // Result is within DST (GMT + 1)
      const result = dayJSAddWithDSTFixed({
        baseDate,
        addParams: [2, 'weeks'],
      });

      // Check that although DST change happened, hours are the same in UTC
      expect(baseDate.utc().hour()).toBe(result.utc().hour());
      expect(result.utc().format()).toBe('2018-04-03T03:00:00Z');
    });

    it(`corrects resulting hour to be the same as in input if start date is within London DST (GMT + 1) 
      and resulting date is after London DST (GMT + 0)`, () => {
      // Base date is within DST: 20th Oct 3:00 (GMT + 1)
      const baseDate = dayjs('2018-10-20 3:00');

      // Result is out of DST change (GMT + 0)
      const result = dayJSAddWithDSTFixed({
        baseDate,
        addParams: [2, 'weeks'],
      });

      // Check that although DST change happened, hours are the same in UTC
      expect(baseDate.utc().hour()).toBe(result.utc().hour());
      expect(result.utc().format()).toBe('2018-11-03T02:00:00Z');
    });

    it('does nothing with hours if both start date and resulting date are within London DST', () => {
      // Base date is within DST: 20th May 3:00 (GMT + 1)
      const baseDate = dayjs('2018-5-20 3:00');

      [
        [24, 'hours'],
        [2, 'weeks'],
        [1, 'months'],
      ].forEach((addParams: Parameters<Dayjs['add']>) => {
        expect(
          dayJSAddWithDSTFixed({
            baseDate,
            addParams,
          })
            .utc()
            .hour()
        ).toBe(baseDate.utc().hour());
      });
    });

    it('does nothing with hours if both start date and resulting date are out of London DST', () => {
      // Base date is out of DST: 20th Jan 3:00 (GMT + 0)
      const baseDate = dayjs('2018-1-20 3:00');

      [
        [24, 'hours'],
        [2, 'weeks'],
        [1, 'months'],
      ].forEach((addParams: Parameters<Dayjs['add']>) => {
        expect(
          dayJSAddWithDSTFixed({
            baseDate,
            addParams,
          })
            .utc()
            .hour()
        ).toBe(baseDate.utc().hour());
      });
    });

    it('adds hours correctly within the same day', () => {
      // Base date is out of DST: 20th Jan 3:00 (GMT + 0)
      const baseDate = dayjs('2018-1-20 3:00');

      expect(
        dayJSAddWithDSTFixed({
          baseDate,
          addParams: [8, 'hours'],
        })
          .utc()
          .hour()
      ).toBe(baseDate.utc().hour() + 8);
    });
  });
});
