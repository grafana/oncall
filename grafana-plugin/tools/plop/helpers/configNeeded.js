module.exports = function configNeeded(options, componentName) {
    const camelCasedName =
        componentName.charAt(0).toLowerCase() + componentName.slice(1);

    if (options.indexOf('add config.ts') !== -1) {
        return `import { ${camelCasedName}Text } from './${camelCasedName}.config';\n`;
    }

    return '';
};
