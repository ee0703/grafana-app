# -*- coding: utf-8 -*-
import json
from django.http import JsonResponse
from django.forms.models import model_to_dict
from qiniu import QcosClient
from .models import Config, get_or_create_config, set_or_create_config


QCOS_API = QcosClient(None)
STACK_NAME = "default"
SERVICE_NAME = "grafana"
IMAGE = "library/grafana:latest"


def index(request):
    data = {"mesage": "Hello, world. You're at the api index.", "status": "ok"}
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
            "instanceNum": params["instanceNum"],
            "envs": ["GF_SECURITY_ADMIN_PASSWORD={}".format(params["password"])],
            "image": IMAGE
        }
    }

    Config.objects.filter(name="status").update(value="creating:stack")
    result = QCOS_API.list_stacks()
    if result[0] is not None and STACK_NAME not in [s["name"] for s in result[0]]:
        QCOS_API.create_stack({"name": STACK_NAME})

    Config.objects.filter(name="status").update(value="creating:service")
    result = QCOS_API.create_service(STACK_NAME, service)
    if result[0] is None:
        Config.objects.filter(name="status").update(value="failed")
        return JsonResponse({"result": "failed creating service"})

    # 接入点和端口设置
    Config.objects.filter(name="status").update(value="creating:network")
    ap = QCOS_API.create_ap({"type": "INTERNAL_IP", "title": "interal_ip"})
    if ap[0] is None:
        Config.objects.filter(name="status").update(value="failed")
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
        Config.objects.filter(name="status").update(value="failed")
        return JsonResponse({"result": "failed creating port"})

    set_or_create_config(name="ip", value=ap[0]["ip"])
    set_or_create_config(name="apid", value=ap[0]["apid"])
    Config.objects.filter(name="status").update(value="deployed")
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