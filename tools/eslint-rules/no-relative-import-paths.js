const path = require('path');

function isParentFolder(path) {
  return path.startsWith('../');
}

function isSameFolder(path) {
  return path.startsWith('./');
}

function getAbsolutePath(relativePath, context) {
  return path.relative(`${context.getCwd()}/src`, path.join(path.dirname(context.getFilename()), relativePath));
}

const message = 'import statements should have an absolute path';

module.exports = {
  meta: {
    type: 'layout',
    fixable: 'code',
  },
  create: function (context) {
    const { allowSameFolder } = context.options[0] || {};

    return {
      ImportDeclaration: function (node) {
        const path = node.source.value;
        if (isParentFolder(path)) {
          context.report({
            node,
            message: message,
            fix: function (fixer) {
              return fixer.replaceTextRange(
                [node.source.range[0] + 1, node.source.range[1] - 1],
                getAbsolutePath(path, context)
              );
            },
          });
        }

        if (isSameFolder(path) && !allowSameFolder) {
          context.report({
            node,
            message: message,
            fix: function (fixer) {
              return fixer.replaceTextRange(
                [node.source.range[0] + 1, node.source.range[1] - 1],
                getAbsolutePath(path, context)
              );
            },
          });
        }
      },
    };
  },
};
