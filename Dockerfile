FROM alpine

RUN echo 'http://mirrors.ustc.edu.cn/alpine/v3.4/main/' | cat - /etc/apk/repositories > temp \
&& mv temp /etc/apk/repositories \
&& apk add --update \
python \
nginx \
python-dev \
py-pip \
sqlite \
tcpflow \
gcc \
musl-dev \
linux-headers \
&& mkdir /run/nginx

COPY agent front requirements.txt start.sh /app/
RUN cd /app \
&& pip install -r requirements.txt  -i http://pypi.douban.com/simple/  --trusted-host pypi.douban.com

COPY conf/nginx.conf /etc/nginx/
COPY conf/uwsgi.ini /app/agent/
COPY conf/settings.py /app/agent/agent

VOLUME ["/data"]

WORKDIR /app
CMD /app/start.sh
