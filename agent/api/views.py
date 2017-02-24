# -*- coding: utf-8 -*-
import json
import traceback
from requests.auth import HTTPBasicAuth
from django.http import JsonResponse
from django.forms.models import model_to_dict
from utils.qcos import QCOS_API, APP_API, Proxy, get_app_info, get_app_key, get_managed
from .models import Config, get_or_create_config, set_or_create_config, update_status

STACK_NAME = "default"
SERVICE_NAME = "grafana-managed"
IMAGE = "library/grafana:latest"


def index(request):
    data = {"message": "Hello, world.", "status": "ok"}
    return JsonResponse(data)

def health_check(request):
    """健康检查"""
    status = get_or_create_config(name="status", value="initialized").value.split(":")[0]
    health_status = ""
    if status == "initialized":
        health_status = "config"
    elif status == "creating":
        health_status = "deploying"
    elif status == "failed":
        health_status = "error"
    else:
        health_status = QCOS_API.get_service_inspect(STACK_NAME, SERVICE_NAME)[0]["status"]
        
    data = {"message": "", "status": health_status}
    return JsonResponse(data)

def status(request):
    """返回当前服务配置状态"""
    data = get_or_create_config(name="status", value="initialized")
    return JsonResponse(model_to_dict(data))


def create_app(request):
    """创建service任务，目前参数仅有password和size"""

    # 仅在initialized状态下才创建service
    status = set_or_create_config(name="status", value="initialized")
    if status.value != "initialized":
        return JsonResponse({"error": "app is creating or already created"}, status=500)

    # 创建 stack， 如果已存在则忽略
    update_status("creating:stack")
    result = QCOS_API.list_stacks()
    if result[0] is not None and STACK_NAME not in [s["name"] for s in result[0]]:
        QCOS_API.create_stack({"name": STACK_NAME})

    # 创建 service, size定死为1U1G
    params = json.loads(request.body.decode("utf-8"))
    service = {
        "name": SERVICE_NAME,
        "spec": {
            "unitType": params["size"],
            "instanceNum": 1,
            "envs": [
                "GF_SECURITY_ADMIN_PASSWORD={}".format(params["password"]),
                "GF_SECURITY_ADMIN_USER=admin"
            ],
            "image": IMAGE
        },
        "volumes": [
            {
            "name": "vol1",
            "mountPath": "/grafana",
            "fsType": "ext4",
            "unitType": "SSD1_10G"
            }
        ],
    }
    update_status("creating:service")
    result = QCOS_API.create_service(STACK_NAME, service)
    if result[0] is None:
        update_status("failed")
        return JsonResponse({"result": "failed creating service", "message": result[1]}, status="500")

    # 保存密码和状态
    set_or_create_config(name="password", value=params["password"])
    update_status("deployed")

    return JsonResponse({"result": "success"})


def _get_service_info(stack, service):
    """"获取grafana服务信息"""
    data = QCOS_API.get_service_inspect(stack, service)
    return data[0]


def service_info(request):
    """"获取grafana服务信息(返回json)"""
    service = _get_service_info(STACK_NAME, SERVICE_NAME)
    service.pop("spec")
    if service:
        return JsonResponse(service, safe=False)
    return JsonResponse({"error": "service not found"}, status=500)


def _get_service_ip(service=None):
    """"获取grafana服务ip地址"""
    service = service or _get_service_info(STACK_NAME, SERVICE_NAME)
    if service is None:
        return None
    return service["containerIps"][0]

def _get_service_password(service=None):
    """获取grafana服务管理员密码"""
    service = service or _get_service_info(STACK_NAME, SERVICE_NAME)
    if service is None:
        return None

    for env in service["spec"]["envs"]:
        if env.startswith("GF_SECURITY_ADMIN_PASSWORD"):
            return env.split("=")[1]

    return None

def access_addr(request):
    """获取grafana访问地址"""
    ip = _get_service_ip()
    if ip is None:
        return JsonResponse({"error": "get service ip error"}, status=500)
    data = QCOS_API.get_web_proxy("%s:3000" % ip)
    return JsonResponse(data[0])


def appauth_status(request):
    return JsonResponse({"status": APP_API is not None })


def get_apps(request):
    """获取app列表(用于自动配置数据源)"""
    if not APP_API:
        return JsonResponse({"error": "no ak/sk config"}, status=500)

    data = APP_API.list_apps()
    apps = data[0]
    if apps is None:
        return JsonResponse({}, status=500)

    apps = [app for app in apps if "vendorUri" not in app or app["vendorUri"]==app["account"]]

    managed = get_managed()
    if managed:
        apps = apps + managed

    apps = make_unique(apps)

    return JsonResponse(apps, safe=False)


def data_sources(request):
    """获取或添加grafana数据源"""
    # 获取grafana服务的访问ip
    ip = _get_service_ip()

    if request.method == 'GET':
        with Proxy("%s:3000" % ip) as (session, vpn_addr):
            password = _get_service_password()

            # import dashbord if needed
            try:
                import_dashboards(ip, password)
            except:
                traceback.print_exc()

            # get the datasources
            url = "%s/api/datasources" % vpn_addr
            ret = session.get(url, auth=HTTPBasicAuth('admin', password))
            data = json.loads(ret.text)
            return JsonResponse({"data": data})
    
    elif request.method == 'POST':
        json_data = json.loads(request.body)
        appuri = json_data.get("appuri")
        if not appuri:
            return JsonResponse({"error": "appuri empty"}, status=400)

        # 获取app信息
        appinfo = get_app_info(appuri)
        if not appinfo:
            return JsonResponse({"error": "app not found"}, status=500)

        # 获取app ak sk
        appkey = get_app_key(appuri)
        if not appkey:
            return JsonResponse({"error": "get app error"}, status=500)

        with Proxy("%s:3000" % ip) as (session, vpn_addr):
            url = "%s/api/datasources" % vpn_addr
            password = _get_service_password()
            datasource = {
                "name": appuri,
                "type": "kirkmonitor",
                "url": "https://kirk-api-%s.qiniu.com/promhub/" % appinfo["region"],
                "access": "proxy",
                "jsonData": {},
                "basicAuth": True,
                "basicAuthUser": appkey["ak"],
                "basicAuthPassword": appkey["sk"]
            }
            ret = session.post(url, json=datasource, auth=HTTPBasicAuth('admin', password))

            if ret.status_code == 200:
                data = json.loads(ret.text)
                return JsonResponse({"data": data})
            else:
                return JsonResponse({"error": "add datasource error", "data": ret.text}, status=500)


def delete_data_source(request, datasource_id):
    
    if request.method != 'DELETE':
        return JsonResponse({"error": "method must be delete"}, status=400)

    if not datasource_id:
        return JsonResponse({"error": "id empty"}, status=400)

    ip = _get_service_ip()
    with Proxy("%s:3000" % ip) as (session, vpn_addr):
        url = "%s/api/datasources/%s" % (vpn_addr, datasource_id)
        password = _get_service_password()
        ret = session.delete(url, auth=HTTPBasicAuth('admin', password))
        if ret.status_code == 200:
            return JsonResponse({"status": "sucess"})
        else:
            return JsonResponse({"error": "delete datasource error", "data": ret.text})


def set_password(request):
    
    if request.method != 'POST':
        return JsonResponse({"error": "method must be post"}, status=400)

    json_data = json.loads(request.body)
    password = json_data.get("password")

    data = {"spec": {"envs": ["GF_SECURITY_ADMIN_PASSWORD={}".format(password)]}}
    ret = QCOS_API.update_service(STACK_NAME, SERVICE_NAME, data)

    if ret[0] is not None:
        return JsonResponse({"status": "sucess"})
    else:
        return JsonResponse({"status": "failed", "message": ret[1]}, status=500)


def make_unique(original_list):
    unique_list = []
    map(lambda x: unique_list.append(x) if (x not in unique_list) else False, original_list)
    return unique_list


def import_dashboards(ip, password):

    with Proxy("%s:3000" % ip) as (session, vpn_addr):

        url = "%s/api/plugins/kirkmonitor/dashboards" % vpn_addr
        ret = session.get(url, auth=HTTPBasicAuth('admin', password))
        dashbords_exist = json.loads(ret.text)

        dashbords = [
            {
                "pluginId": "kirkmonitor",
                "path": u"dashboards/1-1 应用概览.json",
                "overwrite": False,
                "inputs": [{"name":"*","type":"datasource","pluginId":"kirkmonitor","value":""}]
            },
            {
                "pluginId": "kirkmonitor",
                "path": u"dashboards/2-1 服务和容器.json",
                "overwrite": False,
                "inputs": [{"name":"*","type":"datasource","pluginId":"kirkmonitor","value":""}]
            },
            {
                "pluginId": "kirkmonitor",
                "path": u"dashboards/3-1 公网域名.json",
                "overwrite": False,
                "inputs": [{"name":"*","type":"datasource","pluginId":"kirkmonitor","value":""}]
            },
            {
                "pluginId": "kirkmonitor",
                "path": u"dashboards/3-2 公网 IP.json",
                "overwrite": False,
                "inputs": [{"name":"*","type":"datasource","pluginId":"kirkmonitor","value":""}]
            },
            {
                "pluginId": "kirkmonitor",
                "path": u"dashboards/3-3 硬盘空间.json",
                "overwrite": False,
                "inputs": [{"name":"*","type":"datasource","pluginId":"kirkmonitor","value":""}]
            }
        ]

        for ds in dashbords:
            url = "%s/api/dashboards/import" % vpn_addr
            ds_list = [de for de in dashbords_exist if (u"path" in de) and (de[u"path"] == ds["path"]) and de[u"imported"]]
            if len(ds_list) == 0:
                req = session.post(url, json=ds, auth=HTTPBasicAuth('admin', password))
                print req

