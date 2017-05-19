# 使用说明

## step 1 clone 代码

```
git clone git@github.com:kirk-enterprise/grafana-app.git
```


## step 2 构建镜像
```
docker build -t grafana-seed:tagxxx
```

## step 3 推送镜像

用 kirk 登录到 kirk-vendor 账号，然后：
```
kirk images push grafana-seed:tagxxx
```

## step 4 更新spec

使用kirk spec管理工具更新spec，在这之前需要先安装管理工具

```
git clone git@gitlab.qiniu.io:pengquanxin/kirktools.git
cd kirktools
sudo pip install -r requirement.txt
```

然后在配置文件 `config/env.py` 中填入 `kirk-vendor` 的ak、sk，直接`make run`运行即可

```
make run
```

打开 localhost:8086 , 选择 `kirk-vednor.grafana` 这个spec，把spec的镜像名改成刚才推上去的镜像名（grafana-seed:tagxxx）即可


## 附(FAQ)：
1、index.qiniu.com 镜像不能拉取问题  

需要使用 ak/sk 先登录镜像服务器

```
docker login index.qiniu.com
```