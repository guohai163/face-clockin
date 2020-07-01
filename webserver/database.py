# -*- coding:utf8 -*-
import sqlite3

from settings import BASE_DIR


class Database:
    _sql_conn = None
    _cursor = None

    def __init__(self):
        """
        初始化DB
        """
        archive_path = '%s/dbfile/data.sqlit' % BASE_DIR
        self._sql_conn = sqlite3.connect(archive_path)
        self._cursor = self._sql_conn.cursor()
        self._cursor.execute('CREATE TABLE IF NOT EXISTS user_tb (user_code TEXT,base_img TEXT,create_time DATE)')
        self._cursor.execute('CREATE TABLE IF NOT EXISTS clockin_tb (user_code TEXT, user_img TEXT,'
                             'longitude REAL,latitude REAL,local_dist REAL,face_dist REAL,'
                             'create_time DATE)')
        self._sql_conn.commit()

    def get_user_data(self, user_code):
        """
        获取用户文件
        :param user_code:
        :return:
        """
        cursor = self._cursor.execute('SELECT * FROM user_tb WHERE user_code=?', (user_code,)).fetchall()
        if 0 == len(cursor):
            # 没有查到
            return None
        else:
            user_data = {'user_code': cursor[0][0], 'base_img': cursor[0][1],
                         'create_time': cursor[0][2]}
            return user_data

    def create_user_data(self, user_code, base_img):
        """
        创建用户基础数据
        :param user_code:
        :param base_img:
        :return:
        """
        self._cursor.execute('INSERT INTO user_tb VALUES(?,?,datetime(CURRENT_TIMESTAMP, \'localtime\'))',
                             (user_code, base_img,))
        self._sql_conn.commit()

    def add_clockin(self, user_code, user_img, longitude, latitude, local_dist, face_dist):
        """
        用户打卡数据记录
        :param user_code:
        :param user_img:
        :param logitude:
        :param latitude:
        :param local_dist:
        :param face_dist:
        :return:
        """
        sql_parm = (user_code, user_img, longitude, latitude, local_dist, face_dist,)
        self._cursor.execute('INSERT INTO clockin_tb VALUES(?,?,?,?,?,?,datetime(CURRENT_TIMESTAMP, \'localtime\'))',
                             sql_parm)
        self._sql_conn.commit()
