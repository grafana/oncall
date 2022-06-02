module.exports = function createContainerFiles(answers) {
    const actions = [];

    const pathToApp = 'src/containers/{{pascalCase containerName}}';

    const pathToComponentTemplate = 'tools/plop/templates/Container';

    actions.push({
        type: 'add',
        path: `${pathToApp}/{{pascalCase containerName}}.module.css`,
        templateFile: `${pathToComponentTemplate}/Component.module.css.hbs`,
    });

    if (answers.isComponentFunctional) {
        actions.push({
            type: 'add',
            path: `${pathToApp}/{{pascalCase containerName}}.tsx`,
            templateFile: `${pathToComponentTemplate}/FunctionalComponent.tsx.hbs`,
        });
    } else {
        actions.push({
            type: 'add',
            path: `${pathToApp}/{{pascalCase containerName}}.tsx`,
            templateFile: `${pathToComponentTemplate}/ClassComponent.tsx.hbs`,
        });
    }

    return actions;
};
