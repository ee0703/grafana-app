FROM index.qiniu.com/alpine

RUN echo "https://mirrors.ustc.edu.cn/alpine/v3.4/main" > /etc/apk/repositories \
  && echo "https://mirrors.ustc.edu.cn/alpine/v3.4/community" >> /etc/apk/repositories \
  && apk add --update python nginx python-dev py-pip sqlite tcpflow \
  gcc musl-dev linux-headers && \
  rm -rf /var/cache/apk/*

COPY agent /app/agent
COPY front /app/front
COPY requirements.txt start.sh /app/

RUN mkdir /run/nginx \
  && cd /app \
  && pip install -r requirements.txt -i http://pypi.douban.com/simple/ --trusted-host pypi.douban.com

COPY conf/nginx.conf /etc/nginx/
COPY conf/uwsgi.ini /app/agent/
COPY conf/settings.py /app/agent/agent

VOLUME ["/data"]

WORKDIR /app
CMD /app/start.sh
