
import re
import json

from requests import Session
from requests.utils import cookiejar_from_dict
from bs4 import BeautifulSoup

class SteamLibraryControl(object):

    def __init__(self, wa):

        self.wa = wa

        self.library = {}

        self.active_client = None

    def get_app_all(self):

        payload = {
            'tab': 'all'
        }

        url = self.wa.steam_id.community_url + '/games/'

        r = self.wa.session.get(url, params=payload)

        soup = BeautifulSoup(r.text, features="html.parser")

        for s in soup.find_all('script'):
            p = re.compile('var rgGames = (.*?);')
            m = p.search(str(s))
            if m:
                data = json.loads(m.groups()[0])

                self.__populate_library(data)

                return data

        return None

    def __populate_library(self, data):

        for app in data:

            self.library[app['appid']] = {
                'app_id': app['appid'],
                'name': app['name'],
                'logo': app['logo'],
                'friendly_url': app['friendlyURL']
            }

            if app.get('client_summary', None):

                self.library[app['appid']]['state'] = app['client_summary'].get('state', None)
                self.library[app['appid']]['status'] = app['client_summary'].get('status', None)
                self.library[app['appid']]['changing'] = bool(app['client_summary'].get('changing', False))

        return

    def get_app_changing(self):

        url = self.wa.steam_id.community_url + '/getchanging'

        r = self.wa.session.get(url)

        soup = BeautifulSoup(r.text, features="html.parser")

        for s in soup.find_all('script'):
            p = re.compile('UpdateChangingGames(.*?);')
            m = p.search(str(s))
            if m:
                return json.loads(m.groups()[0].replace('({','{').replace('})','}'))

        return None


    def modify_app_state(self, appid, action):

        payload = {
            'sessionid': self.wa.session.cookies.get('sessionid', domain='steamcommunity.com'),
            'appid': appid,
            'operation': action,
        }

        url = 'https://steamcommunity.com/remoteactions/modifyappstate'

        r = self.wa.session.post(url, data=payload)

        return (r.status_code, r.json())
      
if __name__ == '__main__':
    import pprint
    
    pp = pprint.PrettyPrinter(depth=60)

    cookies = 'recentlyVisitedAppHubs=444090%2C730%2C578080%2C755790%2C526870%2C337000; _ga=GA1.2.430523620.1483960082; timezoneOffset=39600,0; steamMachineAuth76561197999943351=320F565FE0D1EA062A8B573E9E93898ABA7DFD42; browserid=1168024375532843940; sessionid=f5ceb6947594b4afaf87eb9e; steamCountry=AU%7Cbc87c363c7947a3386b109aa5618b643; steamLoginSecure=76561197999943351%7C%7CFAFA7F5A56A96A8F8080DC7AC835EA2AC728AE15; app_impressions=330820@2_100300_100500__100503|322500@2_100300_100500__100503; webTradeEligibility=%7B%22allowed%22%3A1%2C%22allowed_at_time%22%3A0%2C%22steamguard_required_days%22%3A15%2C%22new_device_cooldown_days%22%3A7%2C%22time_checked%22%3A1571031267%7D'

    auth = cookiejar_from_dict(dict(p.split('=') for p in cookies.split('; ')))

    slc = SteamLibraryControl(auth)

    pp.pprint(slc.library)

    pp.pprint(slc.modify_app_state(105600, 'uninstall'))
    pp.pprint(slc.get_app_changing())
    # pp.pprint(slc.get_app_all())

