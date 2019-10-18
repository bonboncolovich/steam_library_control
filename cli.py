import cmd
import sys
import dill

from os import path

from getpass import getpass

from steam.webauth import WebAuth
from steam.steamid import SteamID

from steam_library_control import SteamLibraryControl

class SteamLibraryControlCli(cmd.Cmd):
    intro = 'Steam Library Control CLI, ? for help'
    prompt = '(slc) '

    def __init__(self):
        super().__init__()

        self.user = None
        self.slc = None

        if path.exists('session.pkl'):
            print('Existing session found, loading...')
            with open('session.pkl', 'rb') as f:
                auth_session = dill.load(f)

                self.user = WebAuth(auth_session['username'])

                self.user.logged_on = auth_session['logged_on']
                self.user.session_id = auth_session['session_id']
                self.user.steam_id = SteamID(auth_session['steam_id'])
                self.user.session = auth_session['session']

                self.slc = SteamLibraryControl(self.user)

            print(f'Existing session loaded for user: {self.user.username}')
        else:
            print('No session found please login')

    def do_login(self, arg):
        'interactive login to steam, no arguments needed'

        username = input('Enter username: ')
        password = getpass('Enter password: ')

        self.user = WebAuth(username, password)
        self.user.cli_login()

        self.slc = SteamLibraryControl(self.user)

        auth_session = {
            'username': self.user.username,
            'logged_on': self.user.logged_on,
            'session_id': self.user.session_id,
            'steam_id': self.user.steam_id,
            'session': self.user.session
        }

        with open('session.pkl', 'wb') as f:
            dill.dump(auth_session, f)

        return

    def do_user(self, arg):
        'details about the user'

        if not self.user:
            print('No session found, please log in')
            return

        url = 'https://steamcommunity.com/id/bonboncolovich/edit'

        r = self.user.session.get(url)

        print(r.status_code, r.text)

        print('user')
        
        return

    def do_library(self, arg):
        'list all app id\' in the library'

        if not self.slc:
            print('No session found, please log in')
            return

        print(self.slc.get_app_all())

        return

    def do_changing(self, arg):
        'list app id\'s that are changing'

        if not self.slc:
            print('No session found, please log in')
            return

        print(self.slc.get_app_changing())

        return


    def do_install(self, arg):
        'install and app id'

        if not self.slc:
            print('No session found, please log in')
            return

        app_id = arg

        print(self.slc.modify_app_state(app_id, 'install'))

        return

    def do_uninstall(self, arg):
        'list the contents of the library'

        if not self.slc:
            print('No session found, please log in')
            return

        app_id = arg

        print(self.slc.modify_app_state(app_id, 'uninstall'))

        return
        
    def do_quit(self, arg):
        sys.exit()

    def do_q(self, arg):
        sys.exit()

    def do_exit(self, arg):
        sys.exit()

if __name__ == '__main__':
    try:
        SteamLibraryControlCli().cmdloop()
    except KeyboardInterrupt:
        sys.exit()