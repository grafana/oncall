const { createAppAuth } = require("@octokit/auth-app");

(async () => {
  const auth = createAppAuth({
    appId: process.env.GH_APP_ID,
    privateKey: process.env.GH_APP_PRIVATE_KEY,
  });
  const { token, tokenType } = await auth({
    type: "installation",
    installationId: process.env.GH_APP_INSTALLATION_ID,
  });
  const tokenWithPrefix =
    tokenType === "installation" ? `x-access-token:${token}` : token;
  const repositoryUrl = `https://${tokenWithPrefix}@github.com/grafana/ops-devenv.git`;

  const { stdout } = await execa("git", ["clone", repositoryUrl]);
  console.log(stdout);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
