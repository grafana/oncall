module.exports = function createComponentFiles(answers) {
    const actions = [];

    const pathToApp = 'src/components/{{pascalCase componentName}}';

    const pathToComponentTemplate = 'tools/plop/templates/Component';

    actions.push({
        type: 'add',
        path: `${pathToApp}/{{pascalCase componentName}}.module.css`,
        templateFile: `${pathToComponentTemplate}/Component.module.css.hbs`,
    });

    if (answers.isComponentFunctional) {
        actions.push({
            type: 'add',
            path: `${pathToApp}/{{pascalCase componentName}}.tsx`,
            templateFile: `${pathToComponentTemplate}/FunctionalComponent.tsx.hbs`,
        });
    } else {
        actions.push({
            type: 'add',
            path: `${pathToApp}/{{pascalCase componentName}}.tsx`,
            templateFile: `${pathToComponentTemplate}/ClassComponent.tsx.hbs`,
        });
    }

    return actions;
};
