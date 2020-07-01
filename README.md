# 基于人脸打卡项目
## 方案选型
目前通过平面照片来识别的，都是先扫面照片上的人脸，然后在扫面的人脸上打上若干特征点，之后把特点转化为128D的向量。如果两个保存的向量差小于一个阈值我们可以认为这是同一张人脸。我们最终选择了[dlib](http://dlib.net/)这个人脸识别类库，他有C++和Python版本的接口，并支持cuda硬件加速。为了便于快速开发我们肯定会选择Python版本。

先说一下开发环境的准备，dlib可以通过pip的方式来安装，建议使用python3.6以上版本。dlib需要依赖cmake进行编译，如果是mac平台可以通过 brew install cmake 来进行安装。Windows平台需要去[CMake官网](https://cmake.org/download/)下载安装包来进行安装。之后我们再使用`pip install dlib`来安装依赖库。

dlib在做人脸特征点检测时首先需要一个训练好的68个特征点的学习文件[shape_predictor_68_face_landmarks.dat](http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2)以及做向量转化的人脸识别模型[dlib_face_recognition_resnet_model_v1](http://dlib.net/files/dlib_face_recognition_resnet_model_v1.dat.bz2)文件。

接下来我们打开你喜欢用的pythonIDE来准备测试代码的编写。

~~~ python
# -*- coding: UTF-8 -*-
import dlib
import numpy

# 上一步准备好的两个文件
predictor_path = './shape_predictor_68_face_landmarks.dat'
face_rec_model_path = './dlib_face_recognition_resnet_model_v1.dat'
# 准备两个待比较照片
base_pic = './base.jpg'
test_pic = './test.jpg'


# 加载 文件
detector = dlib.get_frontal_face_detector()
sp = dlib.shape_predictor(predictor_path)
facerec = dlib.face_recognition_model_v1(face_rec_model_path)


# 加载基础人脸照片
face_img = dlib.load_rgb_image(base_pic)
# 识别照片中是否有人脸出现
face_dets = detector(face_img, 1)
# 当前不做错误检查，建设基础照片人只有一个需要识别的人脸。识别人脸的68个特征点
shape = sp(face_img, face_dets[0])
# 转化为128维的向量
face_descriptor = facerec.compute_face_descriptor(face_img, shape)
# 转化为numpy数组方便下一步的比较
base_num_array = numpy.array(face_descriptor)
# 以上已经完成基础照片的加载，再两样步骤加载待测试照片

face_img = dlib.load_rgb_image(test_pic)
face_dets = detector(face_img, 1)
shape = sp(face_img, face_dets[0])
face_descriptor = facerec.compute_face_descriptor(face_img, shape)
test_num_array = numpy.array(face_descriptor)

# 进行相似度比较
dist = numpy.linalg.norm(base_num_array - test_num_array)
print('两个人脸相似度为 %f' % dist)
~~~

 把以上代码保存起来比如我们存为main.py，就可以进行测试了 

 ~~~ shell
[root@localhost test]# python3 main.py 
两个人脸相似度为 0.324054
 ~~~

测试的结果为一个0~1之间的浮点数，越接近0证明两个人脸越相似。经我们测试这个数设置在0.4是一个比较理想的值。小于等于0.4即可认为是同一个人


## 性能问题

我们使用单线程进行测试，发现这程序占用CPU好严重，这要是实际应用打卡多人同时打卡的情况CPU不得被使用爆炸了。

![cpu](/doc-pic/2020-06/cpu_top.png)

经过查看主要可优化的部分，首先那两个训练文件巨大肯定要优先修改为程序启动后只加载一次。另外最占CPU时间的就是compute_face_descriptor方法。对于基础照片可以把numpy后的向量数组进行存盘，这次每次只对一张比较照片进行向量化即可。

另外下dlib在使用英伟达家显卡时可以使用GPU进行计算，可以大幅降低CPU的负载。推荐使用类Linux平台来安装cuda驱动。这里我使用centos7为例子进行安装。

~~~ shell
# 首先安装一些依赖要使用的软件
[root@faceid ~]# yum install -y wget pciutils gcc-c++ cmake gcc kernel-devel kernel-headers python3 python3-devel freeglut-devel libX11-devel libXi-devel libXmu-devel make mesa-libGLU-devel libXrender
# 接下来我们确认下机器内的显卡是否为英伟达的
[root@faceid ~]# lspci  | grep -i vga
01:00.0 VGA compatible controller: NVIDIA Corporation GP107 [GeForce GTX 1050 Ti] (rev a1)
07:00.0 VGA compatible controller: NVIDIA Corporation GP107 [GeForce GTX 1050 Ti] (rev a1)

# 屏蔽下系统内的nouveau驱动，启动nvidiafb的驱动
[root@faceid ~]# vi /lib/modprobe.d/dist-blacklist.conf
# 注释掉blacklist nvidiafb并在后面追加两行
#blacklist nvidiafb
blacklist nouveau  
options nouveau modeset=0 

# 重新生成内核并重启
[root@faceid ~]# mv /boot/initramfs-$(uname -r).img /boot/initramfs-$(uname -r).img.bak  
[root@faceid ~]# dracut /boot/initramfs-$(uname -r).img $(uname -r)
[root@faceid ~]# reboot
# 测试下驱动是否屏蔽成功，如果无输出代表屏蔽成功
[root@faceid ~]# dmesg|grep nouveau

# 下载CUDA Toolkit，目前最新版本已经到11了，但我 这里测试对python兼容性不好，推荐使用10.x版本。
# 可以前往这里按你的系统进行下载，对于类Linux系统推荐使用.run的方式下载完整文件
[root@faceid ~]# wget https://developer.nvidia.com/compute/cuda/10.1/Prod/local_installers/cuda_10.1.168_418.67_linux.run
# 增加可执行权限
[root@faceid ~]# chmod +x cuda_10.1.168_418.67_linux.run
# 安装过程中会询问是否要安装nvidia驱动，同意即可
[root@faceid ~]# ./cuda_10.1.168_418.67_linux.run
# 按屏幕最后的提示为你的系统增加相应的环境变量。
[root@faceid ~]# vim ~/.bashrc
# 文件结尾增加
export PATH=/usr/local/cuda-10.1/bin${PATH:+:${PATH}}
export LD_LIBRARY_PATH=/usr/local/cuda-10.1/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
# 全部安装好后我们使用nvidia-smi查看来是否安装正常。
[root@faceid ~]# nvidia-smi 
Mon Jun 29 10:40:44 2020       
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 418.67       Driver Version: 418.67       CUDA Version: 10.1     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  GeForce GTX 105...  Off  | 00000000:01:00.0 Off |                  N/A |
| 40%   34C    P8    N/A /  75W |    288MiB /  4039MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
|   1  GeForce GTX 105...  Off  | 00000000:07:00.0 Off |                  N/A |
| 40%   31C    P8    N/A /  75W |    288MiB /  4040MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
                                                                               
+-----------------------------------------------------------------------------+
| Processes:                                                       GPU Memory |
|  GPU       PID   Type   Process name                             Usage      |
|=============================================================================|
|    0     12810      C   python3                                      278MiB |
|    1     12907      C   python3                                      278MiB |
+-----------------------------------------------------------------------------+
# 如上输出代表已经正常识别到我们的显卡

# 安装cuDNN。前往 https://developer.nvidia.com/cudnn 根据你的CUDA版本下载对应的cuDNN并安装
[root@faceid ~]# tar -xzvf cudnn-10.2-linux-x64-v7.6.5.32.tgz
[root@faceid ~]# cp cuda/include/cudnn.h /usr/local/cuda/include
[root@faceid ~]# cp cuda/lib64/libcudnn* /usr/local/cuda/lib64
[root@faceid ~]# chmod a+r /usr/local/cuda/include/cudnn.h /usr/local/cuda/lib64/libcudnn*

# 如果你和我一样已经安装过dlib了，需要卸载再重新安装dlib才会支持基于cuda的dlib
[root@faceid ~]# pip uninstall dlib
[root@faceid ~]# pip install dlib
# 安装过程中看到如下提示，代码已经启动cuda硬件支持
-- Looking for cuDNN install...
-- Found cuDNN: /usr/local/cuda/lib64/libcudnn.so
-- Enabling CUDA support for dlib.  DLIB WILL USE CUDA
~~~
以上都修改完后我们再重新测试下我们的程序，发现性能提升很多。不再占用CPU时间，而且每次处理都可以控制在毫秒级别。


## 转化为WEB项目

接下为就考虑如何让用户进行打卡了。第一个考虑到的是做手机上的APP，但想到要兼容iOS+Android也是个不小的成本。第二个考虑到的就是做小程序，做成微信的小程序还可以关联到企业微信内，直接就能读取用户在企业内的真实姓名很是方便。那么我们的服务端就要考虑转化为WEB项目。参考了几个python的web框架后发现[tornado]()比较轻量化，更适合我们这种只有接口的项目。

先看下简化版本的流程图，当然如果你想用到实际环境中肯定还要考虑几点到几点算是上班和下班，要给用户不同的提示。以及是否要限制打卡的GPS坐标范围，甚至是连接的网络之类的。

![clockin-process](/doc-pic/2020-06/clockin-process.png)

具体的这块代码比较多不再做更多讲解，我做好一个DEMO放到了github里，大家可以去参考学习[face-clockin项目](https://github.com/guohai163/face-clockin)

## 如何以Docker方式来运行

如果你和我们一样需要使用k8s方式来管理部署服务器，可以还要面临打包成docker镜像的方式来运行。好处多多，再新增加机器只需要安装cuda驱动即可，但dlib、odbc驱动之类的，只要容器里有即可正常使用。

如果想顺利的运行基于cuda的docker需要docker的版本至少是19.03以上。docker的基础名字为[nvidia/cuda](https://hub.docker.com/r/nvidia/cuda)具体要使用的版本看你的需求情况，我这里还是以centos7为例子进行运行。

~~~ shell
# 测试Docker下cuda支持情况
[root@faceid ~]# docker run --rm --gpus all nvidia/cuda:10.1-cudnn7-devel-centos7 nvidia-smi
Tue Jun 30 02:41:20 2020       
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 418.67       Driver Version: 418.67       CUDA Version: 10.1     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  GeForce GTX 105...  Off  | 00000000:01:00.0 Off |                  N/A |
| 40%   32C    P8    N/A /  75W |    288MiB /  4039MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
|   1  GeForce GTX 105...  Off  | 00000000:07:00.0 Off |                  N/A |
| 40%   29C    P8    N/A /  75W |    288MiB /  4040MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
                                                                               
+-----------------------------------------------------------------------------+
| Processes:                                                       GPU Memory |
|  GPU       PID   Type   Process name                             Usage      |
|=============================================================================|
+-----------------------------------------------------------------------------+
~~~

以为上基础，我们来看看咱们项目的Dockerfile应该如何写
~~~ shell
FROM nvidia/cuda:10.1-cudnn7-devel-centos7

MAINTAINER GUOHAI.ORG

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
COPY conf/* ./conf/
RUN mkdir /opt/webserver/uploads

CMD ["python3", "/opt/webserver/main.py"]
~~~

