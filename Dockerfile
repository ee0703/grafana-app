FROM alpine

RUN apk add --update \
    python \
    nginx \
    python-dev \
    py-pip \
    sqlite \
    tcpflow \
    gcc \
    musl-dev   \
    linux-headers \
    && mkdir /run/nginx

WORKDIR /home
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt  -i http://pypi.douban.com/simple/  --trusted-host pypi.douban.com
ADD . /home
ADD conf/nginx.conf /etc/nginx/

RUN cd agent \
    python manage.py makemigrations api \
    python manage.py migrate

CMD /home/start.sh