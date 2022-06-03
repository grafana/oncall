module.exports = function createModelFiles(answers) {
    const actions = [];

    const pathToApp = 'src/models/{{modelName}}';

    const pathToComponentTemplate = 'tools/plop/templates/Model';

    actions.push(
        {
            type: 'add',
            path: `${pathToApp}/{{modelName}}.ts`,
            templateFile: `${pathToComponentTemplate}/BaseModel.ts.hbs`,
        },
        {
            type: 'add',
            path: `${pathToApp}/{{modelName}}.types.ts`,
            templateFile: `${pathToComponentTemplate}/BaseModel.types.ts.hbs`,
        }
    );

    return actions;
};
