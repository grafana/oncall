module.exports = {
  // TODD: enable the before init hooks once grafana/toolkit can limit the jest workers
  git: {
    commitMessage: 'chore: update version',
    tag: false,
    push: false,
    commit: false,
  },
  github: {
    release: false,
  },
  npm: {
    publish: false,
  },
  plugins: {
    '@release-it/conventional-changelog': {
      preset: 'angular',
      infile: 'CHANGELOG.md',
    },
  },
};
