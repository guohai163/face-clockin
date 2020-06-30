# -*- coding:utf8 -*-
from math import radians, cos, sin, asin, sqrt
import numpy


def haversine(lon1, lat1, lon2, lat2):  # 经度1，纬度1，经度2，纬度2 （十进制度数）
    """
    临时方法用来计算两点间距离
    :param lon1:
    :param lat1:
    :param lon2:
    :param lat2:
    :return:
    """
    # 将十进制度数转化为弧度
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine公式
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # 地球平均半径，单位为公里
    return c * r * 1000


def shape_to_np(shape, dtype="int"):
    """
    地址系转化，从dlib转向opencv
    :param shape:
    :param dtype:
    :return:
    """
    # initialize the list of (x, y)-coordinates
    coords = numpy.zeros((68, 2), dtype=dtype)
    # loop over the 68 facial landmarks and convert them
    # to a 2-tuple of (x, y)-coordinates
    for i in range(0, 68):
        coords[i] = (shape.part(i).x, shape.part(i).y)
    # return the list of (x, y)-coordinates
    return coords