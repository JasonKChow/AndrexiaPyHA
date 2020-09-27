import requests as rq
import json
import os.path
from time import time

configPath = './GoogleConfig.json'


class GoogleSmartDevice:

    def __init__(self,
                 config_path: str = configPath,
                 project_id: str = None,
                 client_id: str = None,
                 client_secret: str = None):
        """
        Load or get an authorization config. If a new authorization is being
        made, it needs the project_id, client_id, and client_secret.
        """
        configKeys = ['clientID', 'clientSecret', 'projectID',
                      'accessToken', 'expiresAt', 'refreshToken']
        self.configPath = config_path
        self.baseURL = 'https://smartdevicemanagement.googleapis.com/v1/enterprises/'

        if os.path.isfile(self.configPath):
            with open(self.configPath) as configFile:
                config = json.load(configFile)

                # Check if all config keys are here
                for key in config.keys():
                    if key not in configKeys:
                        raise Exception('Config file missing key.')

            print('Config loaded.')
            self.config = config

        else:
            if project_id is None or client_id is None or client_secret is None:
                raise Exception('Missing authorization args')

            # Create OAuth2 link
            authLink = f'https://nestservices.google.com/partnerconnections/' \
                       f'{project_id}/auth?' \
                       f'redirect_uri=https://www.google.com&' \
                       f'access_type=offline&prompt=consent&' \
                       f'client_id={client_id}' \
                       f'&response_type=code&' \
                       f'scope=https://www.googleapis.com/auth/sdm.service'

            print('Follow the link below and come back with the code')
            print(authLink)

            authCode = input('Auth Code: ')
            while len(authCode) == 0:
                authCode = input('Auth Code: ')

            # Do authorization
            params = {
                'client_id': client_id,
                'client_secret': client_secret,
                'code': authCode,
                'grant_type': 'authorization_code',
                'redirect_uri': 'https://www.google.com'
            }
            r = rq.post('https://www.googleapis.com/oauth2/v4/token',
                        data=params)

            if not r.status_code == 200:
                print(r.text)
                raise Exception('Bad response.')

            # Parse response
            response = r.json()
            accessToken = response['access_token']
            refreshToken = response['refresh_token']
            expiresAt = response['expires_in'] + time()

            # Send device request to finish authorization
            url = f'{self.baseURL}{project_id}/devices'
            headers = {'Content-Type': 'application/json',
                       'Authorization': f'Bearer {accessToken}'}
            r = rq.get(url=url, headers=headers)

            if not r.status_code == 200:
                print(r.text)
                raise Exception('Bad response.')

            config = {
                'clientID': client_id,
                'clientSecret': client_secret,
                'projectID': project_id,
                'accessToken': accessToken,
                'expiresAt': expiresAt,
                'refreshToken': refreshToken
            }

            # Save json
            with open(self.configPath, 'w') as out:
                json.dump(config, out)

            print('Authorization complete.')
            self.config = config

    def _refreshToken(self) -> None:
        # Refresh is not always needed
        if self.config['expiresAt'] > time():
            print('Token still good, no refresh.')
        else:
            # Request new token
            params = {
                'client_id': self.config['clientID'],
                'client_secret': self.config['clientSecret'],
                'refresh_token': self.config['refreshToken'],
                'grant_type': 'refresh_token'
            }
            r = rq.post('https://www.googleapis.com/oauth2/v4/token',
                        data=params)

            if not r.status_code == 200:
                print(r.text)
                raise Exception('Bad response.')

            # Parse response
            response = r.json()
            self.config['accessToken'] = response['access_token']
            self.config['expiresAt'] = response['expires_in'] + time()

            # Save json
            with open(self.configPath, 'w') as out:
                json.dump(self.config, out)

            print('Refresh success.')

    def getStructures(self):
        self._refreshToken()

        url = f"{self.baseURL}{self.config['projectID']}/structures"
        headers = {'Content-Type': 'application/json',
                   'Authorization': f"Bearer {self.config['accessToken']}"}
        r = rq.get(url=url, headers=headers)

        if not r.status_code == 200:
            print(r.text)
            raise Exception('Bad response.')

        return r.json()

    def getDevices(self):
        self._refreshToken()

        url = f"{self.baseURL}{self.config['projectID']}/devices"
        headers = {'Content-Type': 'application/json',
                   'Authorization': f"Bearer {self.config['accessToken']}"}
        r = rq.get(url=url, headers=headers)

        if not r.status_code == 200:
            print(r.text)
            raise Exception('Bad response.')

        return r.json()


if __name__ == '__main__':
    with open('myGoogleCreds.json') as myCredFile:
        myCreds = json.load(myCredFile)

    gsd = GoogleSmartDevice(project_id=myCreds['projectID'],
                            client_id=myCreds['clientID'],
                            client_secret=myCreds['clientSecret'])
