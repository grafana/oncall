const { createAppAuth } = require("@octokit/auth-app");
const { exec } = require("child_process");

(async () => {
  const auth = createAppAuth({
    appId: process.env.GH_APP_ID,
    privateKey: process.env.GH_APP_PRIVATE_KEY,
  });
  const { token, tokenType } = await auth({
    type: "installation",
    installationId: process.env.GH_APP_INSTALLATION_ID,
  });
  console.log("TOOOKEN", token);
  const tokenWithPrefix =
    tokenType === "installation" ? `x-access-token:${token}` : token;
  const repositoryUrl = `https://${tokenWithPrefix}@github.com/grafana/ops-devenv.git`;

  exec(`git clone ${repositoryUrl}`, (error, stdout, stderr) => {
    if (error || stderr) {
      console.error(`Error: ${error.message}`);
      process.exit(1);
    }
    console.log(`stdout: ${stdout}`);
    process.exit(0);
  });
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
