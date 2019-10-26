import os
import errno
import re
import json
import logging
import argparse

import dill

from requests import Session
from bs4 import BeautifulSoup
from steam.webauth import WebAuth
from steam.steamid import SteamID

class WebAuthPersist(WebAuth):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

    def save(self, filename):

        auth_session = {
            'username': self.username,
            'logged_on': self.logged_on,
            'session_id': self.session_id,
            'steam_id': self.steam_id,
            'session': self.session
        }

        with open(filename, 'wb') as f:
            dill.dump(auth_session, f)

        return

    def load(self, filename):

        if not os.path.exists(filename):
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), filename)

        with open(filename, 'rb') as f:
            auth_session = dill.load(f)

            self.username = auth_session['username']
            self.logged_on = auth_session['logged_on']
            self.session_id = auth_session['session_id']
            self.steam_id = SteamID(auth_session['steam_id'])
            self.session = auth_session['session']

            return True


class SteamLibraryControl(object):

    def __init__(self, wa):

        self.wa = wa

        self.library = []
        self.active_client = None
        self.available_disk_space = None

        self.states = [
            'uninstalled',
            'installed',
            'downloading',
            'paused',
            'no_space',
            'invalid_platform',
            'no_remote',
        ]

        self.actions = [
            'install',
            'uninstall',
            'pause',
            'resume'
        ]

    def update(self):

        r = self.__request_games()
        soup = BeautifulSoup(r.text, features="html.parser")

        # print(r.text)

        self.active_client = self.__extract_active_client(soup)
        self.library = self.__extract_library(soup)

    def modify_app_state(self, appid, action):

        if action not in self.actions:
            raise ValueError('Invalid action')

        payload = {
            'sessionid': self.wa.session.cookies.get('sessionid', domain='steamcommunity.com'),
            'appid': appid,
            'operation': action,
        }

        url = 'https://steamcommunity.com/remoteactions/modifyappstate'

        r = self.wa.session.post(url, data=payload)

        return (r.status_code, r.json())

    def __request_games(self):

        payload = {
            'tab': 'all'
        }

        url = self.wa.steam_id.community_url + '/games/'

        r = self.wa.session.get(url, params=payload)

        return r 

    def __extract_active_client(self, soup):
        x = soup.find('p', {'class':'clientConnMachineText'})
        return x.text

    def __extract_library(self, soup):

        for s in soup.find_all('script'):
            p = re.compile('var rgGames = (.*?);')
            m = p.search(str(s))

            if m:
                library = []

                for app in json.loads(m.groups()[0]):

                    library.append({
                        'app_id': app['appid'],
                        'name': app['name'],
                        'logo_url': app['logo'],
                        'last_played': app.get('last_played', 0),
                        'hours_forever': app.get('hours_forever', 0),
                        'state': app.get('client_summary', {}).get('state', 'uninstalled'),
                        'changing': bool(app.get('client_summary', {}).get('changing', False)),
                        'local_content_size': app.get('client_summary', {}).get('local_content_size', None)
                    })

                return library

        return None

    def __request__app_changing(self):

        url = self.wa.steam_id.community_url + '/getchanging'

        r = self.wa.session.get(url)

        soup = BeautifulSoup(r.text, features="html.parser")

        for s in soup.find_all('script'):
            p = re.compile('UpdateChangingGames(.*?);')
            m = p.search(str(s))
            if m:
                data = json.loads(m.groups()[0].replace('({','{').replace('})','}'))

                return data

        return None




def cli_main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    parser = argparse.ArgumentParser(description='Steam Library Control')

    parser.add_argument('--action', '-a', choices=['state', 'install', 'uninstall', 'pause', 'resume'])
    parser.add_argument('--app_id', '-id', type=int)
    parser.add_argument('--login', '-l', action='store_true')
    parser.add_argument('--username', '-u')
    parser.add_argument('--password', '-p')
    parser.add_argument('--load_session', '-ls')
    parser.add_argument('--save_session', '-ss')

    args = parser.parse_args()

    wap = WebAuthPersist('')
    
    if args.load_session:
        logging.info(f'Loading session from file: "{args.load_session}"')
        
        wap.load(args.load_session)
        logging.info(f'Session loaded for user: "{wap.username}"')

    elif args.username and args.password:
            wap = WebAuthPersist(args.username, args.password)

            if not wap.logged_on:
                logging.info('Login failed, interactive login required')

    elif args.login:
        logging.info('Interactive login started')
        username = input('Enter username: ')
        password = getpass('Enter password: ')
        
        wap = WebAuthPersist(username, password)
        wap.cli_login()
        logging.info('Interactive login complete')
        
    else:
        logging.info('No session esablished')


    if wap.logged_on and args.action:

        if args.save_session:
            logging.info(f'Saving session for user: "{wap.username}", session to file: "{args.save_session}"')
            wap.save(args.save_session)
            logging.info(f'Session saved to file: {args.save_session}')

        slc = SteamLibraryControl(wap)
        slc.update()

        if slc.active_client:
            logging.info(f'Connected to library: "{slc.active_client}"')
        else:
            logging.info('No library connected remote control not possible')
        
        if args.action:
            if args.action == 'state':
                logging.info(f'Requesting state for app_id: {args.app_id}')

                format_string = '{:<8} {:60} {:16} {:8}'

                print(format_string.format('app_id', 'name', 'state', 'changing'))

                for d in slc.library:
                    if not args.app_id or d.get('app_id', None) == args.app_id:
                        print(format_string.format(
                                d['app_id'],
                                d['name'],
                                d['state'],
                                'true' if d['changing'] else 'false'
                            ))

            else:
                logging.info(f'Modifying state to: "{args.action}", for app id: "{args.app_id}"...')
                r = slc.modify_app_state(args.app_id, args.action)
                logging.info(f'Result code: {r[1]["success"]}')

    else:
        logging.info('No valid session or command')

if __name__ == "__main__":
    cli_main()
    