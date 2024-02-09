import { ApiSchemas } from 'network/oncall-api/api.types';

export const splitToGroups = (labels: Array<ApiSchemas['LabelKey']>) => {
  return labels.reduce(
    (memo, option) => {
      memo
        .find(({ name }) => name === (option.prescribed ? 'Prescribed' : 'Custom'))
        .options.push({ ...option, data: { isNonEditable: option.prescribed } });

      return memo;
    },
    [
      { name: 'Prescribed', id: 'prescribed', expanded: true, options: [] },
      { name: 'Custom', id: 'custom', expanded: true, options: [] },
    ]
  );
};
