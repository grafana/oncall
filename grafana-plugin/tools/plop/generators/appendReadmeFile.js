module.exports = function createReadmeFiles(answers) {
  const actions = [];

  const pathToApp = 'src';

  const pathToReadmeTemplate = 'tools/plop/templates';

  actions.push({
    type: 'modify',
    path: `${pathToApp}/README.md`,
    pattern: '/* BUILD INFO */',
    templateFile: `${pathToReadmeTemplate}/BuildInfo.md.hbs`,
  });

  return actions;
};
