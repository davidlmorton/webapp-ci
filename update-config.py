#! /usr/bin/env python
from pprint import pprint, pformat
import argparse
import json
import os
import requests
import yaml


class ConfigManager:
    def __init__(self, app, controller_url, admin_pass, config_yaml):
        self._app = app

        self._session = requests.Session()
        self._controller_url = controller_url
        self._token = self._get_api_token(admin_pass)
        self._config = yaml.load(open(config_yaml, 'r').read())

    @property
    def base_config(self):
        return self._config['base_config']

    @property
    def app_values(self):
        return self._config['per_app_values'][self._app]

    @property
    def app_config(self):
        return self._config['per_app_config'][self._app]

    @property
    def env_vars(self):
        return self._config['values_from_env']

    def _get_api_token(self, admin_pass):
        login_url = '%s/v2/auth/login/' % self._controller_url
        headers = {'Content-Type': 'application/json'}
        data = {'username': 'admin', 'password': admin_pass}

        response = self._session.post(login_url, headers=headers,
                data=json.dumps(data))

        if response.status_code != 200:
            self.print_response(response)
            assert response.status_code == 200

        return response.json()['token']

    @staticmethod
    def print_response(response):
        pad = '==========================='
        dpad = pad.replace('=', '-')
        request = response.request
        print("\n#===================================================" + pad)
        print("# %s %s %s" % (response.status_code,
                    request.method, request.url))
        if request.body:
            print("#----------[ Request ]------------------------------" + dpad)
            pprint(json.loads(request.body))
        print("#----------[ Response: %s ]------------------------" %
                response.status_code + dpad)
        try:
            pprint(response.json())
        except json.decoder.JSONDecodeError:
            pprint(response.text)
            pprint(response.headers)

    def _get_new_config(self):
        config = {}
        config.update(self.base_config)
        config.update(self.app_config)
        config['values'].update(self.app_values)

        missing = []
        for name in self.env_vars:
            if name not in os.environ:
                missing.append(name)
            else:
                config['values'][name] = os.environ[name]

        if missing:
            raise RuntimeError("Missing required ENV variables: %s" %
                    pformat(list(missing)))
        else:
            return config

    def _get_current_values(self):
        config_url = '%s/v2/apps/%s/config' % (self._controller_url, self._app)
        headers = {'Authorization': 'token %s' % self._token,
                'Content-Type': 'application/json'}

        response = self._session.get(config_url, headers=headers)

        self.print_response(response)
        assert response.status_code == 200
        return response.json()['values']

    def _get_config_to_post(self):
        new_config = self._get_new_config()
        current_values = self._get_current_values()

        new_value_names = set(new_config['values'].keys())
        current_value_names = set(current_values.keys())

        unset_names = current_value_names - new_value_names
        for name in unset_names:
            new_config['values'][name] = None

        return new_config

    def post_config(self):
        """
        Post the new config taking care to unset variables
        that were set but are no longer being set.
        """
        config_url = '%s/v2/apps/%s/config' % (self._controller_url, self._app)
        data = self._get_config_to_post()
        headers = {'Authorization': 'token %s' % self._token,
                'Content-Type': 'application/json'}

        response = self._session.post(config_url, data=json.dumps(data),
                headers=headers)

        self.print_response(response)

        # deis responds with 409 if you try to post config unchanged.
        assert response.status_code == 201 or response.status_code == 409
        return response.json()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--app', required=True,
            help='The name of the app (ex. empi-sandbox)')
    parser.add_argument('--controller-url', required=True,
            help='The url of the deis controller')
    parser.add_argument('--admin-pass', required=True,
            help='The password for the deis admin user')
    parser.add_argument('--config-yaml', required=True,
            help='A yaml file containing the configuration for your app')
    return parser.parse_args()


if __name__ == '__main__':
    arguments = parse_args()
    config_manager = ConfigManager(**vars(arguments))
    config_manager.post_config()
