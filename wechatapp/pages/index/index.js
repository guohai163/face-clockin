//index.js
// 引用moment插件
const moment = require('../../utils/moment.min.js');
// 引用腾讯地图
const QQMapWX = require('../../utils/qqmap-wx-jssdk.min');
const qqmapsdk = new QQMapWX({ key: 'M4GBZ-Q4XCD-NH344-HBWWH-TFZTE-ZGBON' })
const {
  getUserInfoUrl,
  userLoginUrl
} = require('../../utils/interfaceUrl.js');
const {
  wxRequest
} = require('../../utils/common.js');
// 时间定时器
let dateTimer = null;
//首次加载
let firstLoad = true;
//获取应用实例
const app = getApp()

Page({
  data: {
    hoursVal: '00',
    minutesVal: '00',
    dateVal: '',
    errFlag: false,
    errTip: '',
    userInfoData: {},
    goToWorkData: null,
    offWorkData: null,
    positionFlag: true,//是否进入打卡范围
    isShowGoWorkFlag: true,
    goWorkText: '出勤打卡',
    offWorkText: '下班打卡',
    goToWorkAddress: '',
    offWorkAddress: '',
    curAddress: '',
    isLoad:false
  },

  onLoad: function () {
    this.login();
  },
  onShow: function () {
    if (!firstLoad) {
      console.log('非首次进来')
      this.getLocation();
    }
  },
  onReady(){
    firstLoad = false;
  },
  /**
   * 获取位置 
   */
  getLocation() {
    var _this = this;
    wx.getLocation({
      type: 'gcj02',
      isHighAccuracy: true,
      success: (res) => {
        console.log(res);
        _this.addressParsing(res.latitude, res.longitude);
        _this.getUserInfo(res.latitude, res.longitude);
      },
      fail: () => {
        console.log('定为获取失败')
        _this.againGetLocation();
      }
    })
  },
  /**
   * 首次上传人脸 
   */
  clockinInit(e) {
    console.log('111', e);
    let type = e.currentTarget.dataset.type;
    let _this = this;
    wx.getLocation({
      type: 'gcj02',
      isHighAccuracy: true,
      success: (res1) => {
        wx.navigateTo({
          url: `../index/cameraPage?lon=${res1.longitude}&lat=${res1.latitude}&type=${type}`,
        })
      },
      fail: () => {
        _this.againGetLocation();
      }
    })

  },
    /**
   * 判断登录 
   */
  login() {
    let _this = this;
    if(!wx.getStorageSync('userCode')){
      wx.login({
        success: function (res) {
          if (res.code) {
            //TODO: 此处为了减化业务暂时把code当做user_code使用
            console.info('登录成功'+res.code)
            wx.setStorageSync("userCode", res.code);            
          } else {
            console.log('登录失败！' + res.errMsg)
          }
        }
      });
    }
    else{
      _this.getLocation();
    }
  },
    /**
   * 二次获取定位 
   */
  againGetLocation() {
    var _this = this;
    wx.showModal({
      title: '请求授权当前位置',
      content: '需要获取您的地理位置，或需要您手动打开企业微信定位授权',
      success: function (res) {
        if (res.confirm) {
          //确定授权，通过wx.openSetting发起授权请求
          wx.openSetting({
            success: function () {
              _this.getLocation();
            }
          })
        } else {
          _this.getLocation();
        }
      }
    })
  },
  /**
   * 地址解析 
   */
  addressParsing(latitude, longitude, type) {
    let _this = this;
    qqmapsdk.reverseGeocoder({
      location: {
        latitude,
        longitude
      },
      success(address) {
        if (type === 'goToWork') {
          _this.setData({
            goToWorkAddress: address.result.formatted_addresses.recommend
          })
        } else if (type === 'offWork') {
          _this.setData({
            offWorkAddress: address.result.formatted_addresses.recommend
          })
        } else {
          _this.setData({
            curAddress: address.result.formatted_addresses.recommend
          })
        }
      }
    })
  },
    /**
   * 获取用户登录信息 
   */
  async getUserInfo(lat, lon) {
    if (wx.getStorageSync("userCode")) {
      wx.showLoading({
        mask: true
      })
      setTimeout(() => {
        wx.hideLoading();
      }, 3000)
      let { data } = await wxRequest(getUserInfoUrl, 'GET', {
        userCode: wx.getStorageSync("userCode"),
        lat,
        lon
      }, false)
      console.log(data);
      wx.hideLoading();
      if (data.data == 'not_fond_user') {
        // 待初始化
        let userInfo = {'baseImg': false, 'trueName': '你好：', 'department': '欢迎使用公司打卡程序'}
        this.setData({
          userInfoData: userInfo,
          isLoad: true
        })
      } else {
        // 已经存在的用户
        let userInfo = {'baseImg': true, 'trueName': '你好：', 'department': '欢迎使用公司打卡程序'}
        this.setData({
          userInfoData: userInfo,
          positionFlag: data.distance
        })
      }
      this.dateTimeInit(data.now)
    } else {
      this.setData({
        errFlag: true,
        errTip: '获取信息失败'
      })
    }
  },
  dateTimeInit(time) {
    let curTime = moment(time).valueOf();
    this.setData({
      dateVal: moment(curTime).format('YYYY.MM.DD'),
      hoursVal: moment(curTime).format('HH'),
      minutesVal: moment(curTime).format('mm')
    })
    if (this.data.userInfoData.baseImg) {
      if (dateTimer) clearInterval(dateTimer);
      dateTimer = setInterval(() => {
        curTime += 1000;
        this.setData({
          hoursVal: moment(curTime).format('HH'),
          minutesVal: moment(curTime).format('mm')
        })
      }, 1000)
    }
  },
  onUnload() {
    clearInterval(dateTimer);
  }
})
