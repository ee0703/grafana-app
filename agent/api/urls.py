from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^status$', views.status, name='status'),
    url(r'^kirk/create_app$', views.create_app, name='create_app'),
    url(r'^kirk/service_info$', views.service_info, name='service_info'),
    url(r'^kirk/access_addr$', views.access_addr, name='access_addr'),
    url(r'^kirk/ap_info$', views.ap_info, name='ap_info'),
    url(r'^healthcheck$', views.health_check, name='health_check'),
    url(r'^kirk/apps$', views.get_apps, name='get_apps'),
]