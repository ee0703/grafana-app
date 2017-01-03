import requests
import os
from qiniu.services.compute import app
from qiniu.auth import QiniuMacAuth
from qiniu import QcosClient


class Proxy(object):
    def __init__(self, obj, entry):
        self.session = requests.Session()
        self.entry= entry

    def __enter__(self):
        self.session.get(self.entry)
        return self.session

    def __exit__(self, type, value, traceback):
        pass


def get_account_auth():
    ak = os.environ.get("USER_ACCOUNT_AK", None)
    sk = os.environ.get("USER_ACCOUNT_SK", None)
    if not ak or not sk:
        return None
    return QiniuMacAuth(ak, sk)


QCOS_API = QcosClient(None)
acc_auth = get_account_auth()
APP_API = app.AccountClient(acc_auth, "https://app-api.qiniu.com") if acc_auth else None