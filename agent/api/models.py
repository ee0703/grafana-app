from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Config(models.Model):
    name = models.CharField(max_length=50, unique=True)
    value = models.CharField(max_length=100)

    class Meta:
        db_table = "app_config"
        managed = True


def get_or_create_config(name, value):
    cfg = Config.objects.filter(name=name)
    if not cfg:
        cfg = Config(name=name, value=value)
        cfg.save()
        return cfg
    else:
        return cfg[0]


def set_or_create_config(name, value):
    cfg = Config.objects.filter(name=name)
    if not cfg:
        cfg = Config(name=name, value=value)
        cfg.save()
        return cfg
    else:
        cfg[0].value = value
        cfg[0].save()
        return cfg[0]

    
def update_status(value):
    return Config.objects.filter(name="status").update(value=value)
