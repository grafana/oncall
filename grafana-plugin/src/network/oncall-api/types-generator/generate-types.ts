import openapiTS, { astToString } from 'openapi-typescript';

import type { CustomApiSchemas } from './custom-schemas';

import fs from 'fs';

// They need to match with any custom schema added to CustomApiSchemas type in ./api.types.ts
const CUSTOMIZED_SCHEMAS: Array<keyof CustomApiSchemas> = ['Alert', 'AlertGroup'];

export const addCustomSchemasToAutogeneratedOutput = (
  originalOutput: string,
  customizedSchemas: string[] = CUSTOMIZED_SCHEMAS
) => {
  const REGEX = new RegExp(`\\s(${customizedSchemas.join('|')})\\s*:`, 'g');

  let newOutput = `
    import type { CustomApiSchemas } from './types-generator/custom-schemas.d.ts';

    ${originalOutput}
  `;
  newOutput = newOutput.replace(REGEX, (match) =>
    match.concat(` CustomApiSchemas["${match.split(':')[0].trim()}"] & `)
  );

  return newOutput;
};

(async () => {
  const ast = await openapiTS(new URL('http://localhost:8080/internal/schema/'));
  const output = astToString(ast);

  fs.writeFileSync(
    '../autogenerated-api.types.d.ts',
    addCustomSchemasToAutogeneratedOutput(output, CUSTOMIZED_SCHEMAS)
  );
})();
