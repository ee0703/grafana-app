# -*- coding: utf-8 -*-
import json
from django.http import JsonResponse
from django.forms.models import model_to_dict
from utils.qcos import QCOS_API, APP_API, Proxy
from .models import Config, get_or_create_config, set_or_create_config, update_status

STACK_NAME = "default"
SERVICE_NAME = "grafana-managed"
IMAGE = "library/grafana:latest"


def index(request):
    data = {"message": "Hello, world.", "status": "ok"}
    return JsonResponse(data)

def health_check(request):
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
    data = get_or_create_config(name="status", value="initialized")
    return JsonResponse(model_to_dict(data))


def create_app(request):
    status = set_or_create_config(name="status", value="initialized")
    if status.value != "initialized":
        return JsonResponse({"error": "app is creating or already created"}, status=500)

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
        }
    }

    update_status("creating:stack")
    result = QCOS_API.list_stacks()
    if result[0] is not None and STACK_NAME not in [s["name"] for s in result[0]]:
        QCOS_API.create_stack({"name": STACK_NAME})

    update_status("creating:service")
    result = QCOS_API.create_service(STACK_NAME, service)
    if result[0] is None:
        update_status("failed")
        return JsonResponse({"result": "failed creating service"})

    # 接入点和端口设置
    update_status("creating:network")
    ap = QCOS_API.create_ap({"type": "INTERNAL_IP", "title": "interal_ip"})
    if ap[0] is None:
        update_status("failed")
        return JsonResponse({"result": "failed creating ap"})

    port_cfg = {
        "proto": "HTTP",
        "backendPort": 3000, 
        "backends": [
            {
                "stack": STACK_NAME,
                "service": SERVICE_NAME,
                "weight":10000
            }
        ]
    }
    result = QCOS_API.set_ap_port(ap[0]["apid"], 80, port_cfg)
    if result[0] is None:
        update_status("failed")
        return JsonResponse({"result": "failed creating port"})

    set_or_create_config(name="ip", value=ap[0]["ip"])
    set_or_create_config(name="apid", value=ap[0]["apid"])
    update_status("deployed")
    return JsonResponse({"result": "success"})


def service_info(request):
    data = QCOS_API.get_service_inspect(STACK_NAME, SERVICE_NAME)
    if data[0]:
        return JsonResponse(data[0], safe=False)
    return JsonResponse({"error": "service not found"}, status=404)


def ap_info(request):
    ip = Config.objects.get(name="ip").value
    apid = Config.objects.get(name="apid").value
    return JsonResponse({"ip": ip, "apid": apid})


def access_addr(request):
    ip = Config.objects.get(name="ip").value
    data = QCOS_API.get_web_proxy("%s:80" % ip)
    return JsonResponse(data[0])


def get_apps(request):
    data = APP_API.list_apps()
    apps = data[0]
    if apps is None:
        return JsonResponse({}, status=500)
    return JsonResponse(apps, safe=False)


def get_data_sources(request):
    with Proxy() as session:
        data = session.get("/api/datasources")
        return JsonResponse({"data": str(data)})
