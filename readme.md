# Steam Library Control

A command line tool for interacting with the undocumented steam remote actions api. The tool allows the user to install and uninstall applications on a currently active steam desktop client, it uses the login credentials of the steam account to create and optionally save a session for later use.

Requirements are Python 3.6+ and the modules specified in `reqirements.txt`.

## Authentication

To issue commands to control the library first an authenticated session has to be established. The simplest way is to call `python3 steam_library_control.py --login` which will provide an series of interactive prompts to authenticate this allows for the handling of 2FA and CAPTCHA. Alterntively you can call `python3 steam_library_control.py --username <username> --password <password>` if there is no 2FA required.

## Session storage and recall

Saving authenticated sessions allows for them to be reused for future commands. To save use the argument `--save-session <filename>` when authenticating. Then when running commands use `--load-session <filename>` to recall the session.

## Example commands

- `python3 steam_library_control.py --load-session <filename> --action state` - List the state of all games in the active desktop client.

- `python3 steam_library_control.py --load-session <filename> --action install --id <app-id>` - Install a specific app id to the active desktop client.

- `python3 steam_library_control.py --load-session <filename> --action uninstall --id <app-id>` - Uninstall a specific app id from the active desktop client.
