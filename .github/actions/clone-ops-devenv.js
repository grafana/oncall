const { createAppAuth } = require("@octokit/auth-app");
const { exec } = require("child_process");

const cloneRepo = async (name) =>
  new Promise((resolve, reject) => {
    exec(`git clone ${name}.git`, (error, stdout, stderr) => {
      if (error) {
        console.error(`Error: ${JSON.stringify(error)}`);
        reject(error);
        return;
      }
      if (stderr) {
        console.error(`stderr: ${stderr}`);
        reject(stderr);
        return;
      }
      console.log(`stdout: ${stdout}`);
      resolve(stdout);
    });
  });

(async () => {
  const auth = createAppAuth({
    appId: process.env.GH_APP_ID,
    privateKey: process.env.GH_APP_PRIVATE_KEY,
  });
  await auth({
    type: "installation",
    installationId: process.env.GH_APP_INSTALLATION_ID,
  });

  await cloneRepo("ops-devenv");
  await cloneRepo("gops-labels");
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
