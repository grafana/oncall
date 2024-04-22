const { createAppAuth } = require("@octokit/auth-app");
const { exec } = require("child_process");

/**
  https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation#using-octokitjs-to-authenticate-with-an-installation-id
  https://www.npmjs.com/package/@octokit/auth-app#authenticate-as-installation
*/

const cloneRepo = async (name, installationToken) =>
  new Promise((resolve, reject) => {
    exec(
      `git clone https://x-access-token:${installationToken}@github.com/grafana/${name}.git`,
      (error, stdout, stderr) => {
        if (error) {
          console.error(`Error: ${JSON.stringify(error)}`);
          // reject(error);
          // return;
        }
        if (stderr) {
          console.error(`stderr: ${stderr}`);
          // reject(stderr);
          // return;
        }
        console.log(`stdout: ${stdout}`);
        resolve(stdout);
      }
    );
  });

(async () => {
  const auth = createAppAuth({
    appId: process.env.GH_APP_ID,
    privateKey: process.env.GH_APP_PRIVATE_KEY,
  });
  const { token: installationToken } = await auth({
    type: "installation",
    installationId: process.env.GH_APP_INSTALLATION_ID,
  });

  await cloneRepo("ops-devenv", installationToken);
  await cloneRepo("gops-labels", installationToken);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
