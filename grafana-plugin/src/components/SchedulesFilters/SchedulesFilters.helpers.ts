import moment from 'moment';

export function optionToDateString(option: string) {
  switch (option) {
    case 'today':
      return moment().startOf('day').format('YYYY-MM-DD');
    case 'tomorrow':
      return moment().add(1, 'day').startOf('day').format('YYYY-MM-DD');
    default:
      return moment().add(2, 'day').startOf('day').format('YYYY-MM-DD');
  }
}

export function dateStringToOption(dateString: string) {
  const today = moment().startOf('day').format('YYYY-MM-DD');
  if (dateString === today) {
    return 'today';
  }
  const tomorrow = moment().add(1, 'day').startOf('day').format('YYYY-MM-DD');
  if (dateString === tomorrow) {
    return 'tomorrow';
  }

  return 'custom';
}
