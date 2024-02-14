import { ApiSchemas } from 'network/oncall-api/api.types';

export const splitToGroups = (labels: Array<ApiSchemas['LabelKey']>) => {
  return labels.reduce(
    (memo, option) => {
      memo
        .find(({ name }) => name === (option.prescribed ? 'System' : 'User added'))
        .options.push({ ...option, data: { isNonEditable: option.prescribed } });

      return memo;
    },
    [
      { name: 'System', id: 'system', expanded: true, options: [] },
      { name: 'User added', id: 'user_added', expanded: true, options: [] },
    ]
  );
};
