import requests
import os
from qiniu import http
from qiniu.services.compute import app
from qiniu.auth import QiniuMacAuth
from qiniu import QcosClient


class Proxy(object):
    def __init__(self, entry):
        self.session = requests.Session()
        self.entry = entry

    def __enter__(self):
        data = QCOS_API.get_web_proxy(self.entry)
        url = data[0]["oneTimeUrl"]
        req = self.session.get(url)
        url_ret = req.url.rstrip('/')
        return self.session, url_ret

    def __exit__(self, type, value, traceback):
        pass


def get_account_auth():
    ak = os.environ.get("USER_ACCOUNT_AK", None)
    sk = os.environ.get("USER_ACCOUNT_SK", None)
    if not ak or not sk:
        return None
    return QiniuMacAuth(ak, sk)


def get_app_info(appuri):
    if ACC_AUTH is None:
        return None
    url = '{0}/v3/apps/{1}'.format(APP_HOST, appuri)
    return http._get_with_qiniu_mac(url, None, ACC_AUTH)[0]


def get_app_key(appuri):
    if ACC_AUTH is None:
        return None
    keys = APP_API.get_app_keys(appuri)[0]
    keys = [item for item in keys if item["state"] == "enabled"]
    return keys[0] if len(keys) > 0 else None


APP_HOST = "https://app-api.qiniu.com"
QCOS_API = QcosClient(None)
ACC_AUTH = get_account_auth()
APP_API = app.AccountClient(ACC_AUTH, APP_HOST) if ACC_AUTH else None