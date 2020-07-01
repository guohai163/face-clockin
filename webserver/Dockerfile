FROM nvidia/cuda:10.1-cudnn7-devel-centos7

MAINTAINER GYDEV.CN

WORKDIR /opt

RUN yum -y install  gcc-c++ cmake gcc kernel-devel kernel-headers git  python3 python3-devel freeglut-devel libX11-devel libXi-devel libXmu-devel make mesa-libGLU-devel gcc-c++ libXrender && \
    git clone https://github.com/davisking/dlib.git && \
    cd dlib && python3 setup.py install
RUN yum -y install unixODBC unixODBC-devel && \
    curl -O https://cdn.mysql.com//Downloads/Connector-ODBC/8.0/mysql-connector-odbc-8.0.20-1.el7.x86_64.rpm && \
    rpm -ivh mysql-connector-odbc-8.0.20-1.el7.x86_64.rpm && \
    myodbc-installer -d -l

WORKDIR /opt/webserver

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

COPY *.py ./
COPY dlib_dat/*.dat ./dlib_dat/
RUN mkdir uploads
RUN mkdir dbfile

CMD ["python3", "/opt/webserver/main.py"]