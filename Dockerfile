FROM httpd:2.4.33

RUN apt-get update
RUN apt-get -y install python3.4 python3-pip libapache2-mod-wsgi-py3 libxml2-dev libxslt1-dev lib32z1-dev libjpeg-dev libmagic-dev  python-dev vim

RUN mkdir -p /opt/python/current/app
COPY . /opt/python/current/app
WORKDIR /opt/python/current/app
RUN pip3 install -r requirements.txt

RUN ln -s /usr/local/apache2/conf/ /etc/httpd
RUN ln -s /usr/local/apache2/modules /etc/httpd/modules
RUN ln -s /usr/lib/apache2/modules/mod_wsgi.so /etc/httpd/modules/mod_wsgi.so
RUN mkdir /var/run/httpd
RUN ln -s /var/run/httpd /etc/httpd/run
RUN mkdir /var/www
RUN ln -s /usr/local/apache2/htdocs /var/www/html
RUN ln -s /usr/local/apache2/logs /var/log/httpd
RUN ln -s /var/log/httpd /etc/httpd/logs
RUN mkdir /etc/httpd/conf.d

COPY .ebextensions/http/conf/httpd.conf /etc/httpd/httpd.conf
RUN sed -i 's/User apache/User daemon/g' /etc/httpd/httpd.conf
RUN sed -i 's/Group apache/Group daemon/g' /etc/httpd/httpd.conf
COPY .ebextensions/http/conf.d/* /etc/httpd/conf.d
COPY docker-files/wsgi.conf /etc/httpd/conf.d

WORKDIR /etc/httpd/
COPY docker-files/conf.modules.d.tar.gz /tmp/
RUN tar zxvf /tmp/conf.modules.d.tar.gz



#RUN rm /etc/nginx/conf.d/*.conf
#COPY .ebextensions/nginx/conf.d/*.conf /etc/nginx/conf.d/
#COPY .ebextensions/nginx/conf.d/elasticbeanstalk /etc/nginx/conf.d/elasticbeanstalk
EXPOSE 80
