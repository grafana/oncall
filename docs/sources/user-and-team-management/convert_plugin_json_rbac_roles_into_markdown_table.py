"""
Use this utility script to convert the Grafana OnCall's RBAC roles, defined in its plugin.json,
into a Markdown table for public documentation purposes.

It will automatically copy the compiled markdown table to your OS's clipboard. You can simply paste it into the docs
(NOTE: the clipboard functionality was only tested on Mac, mileage may vary on Windows/Linx. If the subprocess
call fails, simply modify the script to print out the contents to the console)
"""

import json
import subprocess

txt = "| Role | Description | Granted Actions | Basic Roles Granted To |\n| -- | -- | -- | -- |\n"

PLUGINS_APP_ACCESS_ACTION = "plugins.app:access"

with open("../../../grafana-plugin/src/plugin.json") as ifp:
    data = json.load(ifp)

    for role in data["roles"]:
        basic_role_grants = ", ".join(
            role["grants"]) if role["grants"] else "N/A"
        role = role["role"]

        permissions = ""
        granted_permissions = role["permissions"]
        num_permissions = len(granted_permissions)

        for idx, permission in enumerate(granted_permissions, start=1):
            action = permission["action"]

            if action != PLUGINS_APP_ACCESS_ACTION:
                permissions += f"`{action}`"

                if idx != num_permissions:
                    permissions += "<br /><br />"

        txt += f"| {role['name']} | {role['description']} | {basic_role_grants} | {permissions}\n"

subprocess.run("pbcopy", text=True, input=txt)
