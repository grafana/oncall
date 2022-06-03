module.exports = [
    {
        type: 'input',
        name: 'modelName',
        message: 'Model name please (snake_case)',
        filter: value => value.toLowerCase(),
    },
];
