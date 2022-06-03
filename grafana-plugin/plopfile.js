const createComponentFiles = require('./tools/plop/generators/createComponentFiles');
const createContainerFiles = require('./tools/plop/generators/createContainerFiles');
const createModelFiles = require('./tools/plop/generators/createModelFiles');
const appendReadmeFile = require('./tools/plop/generators/appendReadmeFile');
const componentPrompts = require('./tools/plop/prompts/componentPrompts');
const containerPrompts = require('./tools/plop/prompts/containerPrompts');
const modelPrompts = require('./tools/plop/prompts/modelPrompts');
const readmePrompts = require('./tools/plop/prompts/readmePrompts');

// const configNeededHelper = require('./tools/plop/helpers/configNeeded');

module.exports = function plopGenerator(plop) {
  plop.setWelcomeMessage('What can I do for you?');

  // plop.setHelper('configNeeded', configNeededHelper);

  plop.setGenerator('Create model files', {
    description: 'Create model',
    prompts: modelPrompts,
    actions: (answers) => createModelFiles(answers),
  });

  plop.setGenerator('Create component files', {
    description: 'Create component and CSS module for it',
    prompts: componentPrompts,
    actions: (answers) => createComponentFiles(answers),
  });

  plop.setGenerator('Create container files', {
    description: 'Create component connected to store',
    prompts: containerPrompts,
    actions: (answers) => createContainerFiles(answers),
  });

  plop.setGenerator('Append build info', {
    description: 'Add build info to plugin readme',
    prompts: readmePrompts,
    actions: (answers) => appendReadmeFile(answers),
  });
};
