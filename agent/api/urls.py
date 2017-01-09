from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^status$', views.status, name='status'),
    url(r'^appauth_status$', views.appauth_status, name='appauth_status'),
    url(r'^kirk/create_app$', views.create_app, name='create_app'),
    url(r'^kirk/service_info$', views.service_info, name='service_info'),
    url(r'^kirk/access_addr$', views.access_addr, name='access_addr'),
    url(r'^healthcheck$', views.health_check, name='health_check'),
    url(r'^kirk/apps$', views.get_apps, name='get_apps'),
    url(r'^grafana/data_sources$', views.data_sources, name='data_sources'),
    url(r'^grafana/data_sources/(?P<datasource_id>[^\/]+)$', views.delete_data_source, name='delete_data_source'),
]