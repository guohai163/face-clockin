# -*- coding:utf8 -*-
import json
import os
import uuid
import dlib
import numpy
import tornado.web
import time

from database import Database
from settings import BASE_DIR, UPLOADS_DIR, COMP_LOCATION, ALLOW_DIST

# 人脸学习文件
from utils import haversine

predictor_path = '%s/dlib_dat/shape_predictor_68_face_landmarks.dat' % BASE_DIR
face_rec_model_path = '%s/dlib_dat/dlib_face_recognition_resnet_model_v1.dat' % BASE_DIR

# 加载dlib初始文件，保证在整个web生命周期只加载一次
detector = dlib.get_frontal_face_detector()
sp = dlib.shape_predictor(predictor_path)
facerec = dlib.face_recognition_model_v1(face_rec_model_path)

DBOBJ = Database()


def export_face_descriptor(face_file, user_code=None):
    """
    第一版的向量生成方法，先使用基于文件的
    :param user_code:
    :param face_file:
    :return:
    """
    # 加载人脸图片，变更格式为numpy
    face_img = dlib.load_rgb_image(face_file)
    # 识别人脸位置,只取识别出来的第一张人脸
    face_dets = detector(face_img, 1)
    if len(face_dets) != 1:
        return 'not-fond-face', None
    # 识别人脸的68个特征点
    shape = sp(face_img, face_dets[0])
    # 转化为128维的向量
    face_descriptor = facerec.compute_face_descriptor(face_img, shape)
    num_array = numpy.array(face_descriptor)
    return '', num_array


def save_image(user_code, file_meta):
    """
    保存用户上传的文件
    :param user_code:
    :param file_meta:
    :return:
    """
    # 获得文件扩展名
    suffix = file_meta['filename'].split('.')[-1]
    new_filename = '%s.%s' % (str(uuid.uuid1()), suffix)
    user_dir = '%s/%s' % (UPLOADS_DIR, user_code)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    f = open('%s/%s' % (user_dir, new_filename), 'wb')
    f.write(file_meta['body'])
    f.close()
    return new_filename


class StatusHandler(tornado.web.RequestHandler):
    """
    用户数据状态类，检查用户是否进行过初始化操作
    """

    def get(self):
        result_data = {'state': 'fail', 'data': '', 'distance': False, 'now': 0}
        user_code = self.request.headers.get('user-code')
        user_data = DBOBJ.get_user_data(user_code)
        if None is user_data or user_data['base_img'] == '':
            # 没有用户
            result_data['state'] = 'success'
            result_data['data'] = 'not_fond_user'
        else:
            # 已经存在用户
            result_data['state'] = 'success'
            result_data['data'] = 'have_user'
        if 'lon' in self.request.arguments:
            lon2 = float(self.get_argument('lon', 0.0))
            lat2 = float(self.get_argument('lat', 0.0))
            local_dist = haversine(COMP_LOCATION['lon'], COMP_LOCATION['lat'], lon2, lat2)
            if local_dist > ALLOW_DIST:
                result_data['distance'] = False
            else:
                result_data['distance'] = True
        result_data['now'] = int(round(time.time() * 1000))
        self.write(result_data)


class InitHandler(tornado.web.RequestHandler):
    """
    初始化操作类，存储用户头像
    """

    def post(self):
        result_data = {'state': 'fail', 'data': ''}
        user_code = self.request.headers.get('user-code')
        user_data = DBOBJ.get_user_data(user_code)
        if None is not user_data:
            result_data['data'] = 'user-have'
            self.write(json.dumps(result_data))
            return

        meta = self.request.files['file'][0]
        user_face = save_image(user_code, meta)
        msg, face_array = export_face_descriptor('%s/%s/%s' % (UPLOADS_DIR, user_code, user_face), user_code)
        if face_array is None:
            result_data['data'] = msg
            self.write(result_data)
            return
        # 保存向量文件
        face_array.tofile('%s/%s/facebase.bin' % (UPLOADS_DIR, user_code))
        # 操作数据存储
        DBOBJ.create_user_data(user_code, user_face)
        result_data['state'] = 'success'
        result_data['data'] = 'init success'
        self.write(result_data)


class ClockHandler(tornado.web.RequestHandler):
    """
    打卡操作类，只提供POST方法，提交照片并返回识别率
    """

    def post(self):
        result_data = {'state': 'fail', 'data': ''}
        # 获取参数
        user_ip = self.request.remote_ip
        user_code = self.request.headers.get('user-code')
        if 'lon' in self.request.arguments:
            lon = float(self.get_argument('lon', 0.0))
            lat = float(self.get_argument('lat', 0.0))
        else:
            result_data['data'] = 'log-or-lat-error'
            self.write(json.dumps(result_data))
            return

        # 检查距离
        local_dist = haversine(COMP_LOCATION['lon'], COMP_LOCATION['lat'], lon, lat)
        if local_dist > ALLOW_DIST:
            result_data['data'] = 'gps-location-overstep'
            self.write(json.dumps(result_data))
            return

        user_data = DBOBJ.get_user_data(user_code)
        if None is user_data:
            result_data['data'] = 'user-not-init'
            self.write(json.dumps(result_data))
            return

        if None is user_data['base_img'] or '' == user_data['base_img']:
            result_data['data'] = 'user-not-init-face'
            self.write(json.dumps(result_data))
            return

        face_base = numpy.fromfile('%s/%s/facebase.bin' % (UPLOADS_DIR, user_code))
        meta = self.request.files['file'][0]
        user_face = save_image(user_code, meta)
        msg, face_array = export_face_descriptor('%s/%s/%s' % (UPLOADS_DIR, user_code, user_face), user_code)
        if face_array is None:
            result_data['data'] = msg
            self.write(result_data)
            return
        dist = numpy.linalg.norm(face_base - face_array)
        # 检查人脸相似度
        if dist > 0.4:
            result_data['data'] = 'face-dist-overstep'
            self.write(json.dumps(result_data))
            return

        DBOBJ.add_clockin(user_code, user_face, lon, lat, local_dist, dist)
        result_data['state'] = 'success'
        if result_data['data'] == '':
            result_data['data'] = 'OK'
        self.write(result_data)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('face check program by python,glib')
