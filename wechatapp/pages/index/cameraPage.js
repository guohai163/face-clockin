const {
  clockinInitUrl,
  clockinUrl
} = require('../../utils/interfaceUrl.js');
let isShowTitle = true;
Page({

  /**
   * 页面的初始数据
   */
  data: {
    lon: null,
    lat: null,
    type: null,
    cameraFlag: true
  },
  /**
   * 生命周期函数--监听页面加载
   */
  onLoad: function (options) {
    isShowTitle = true;
    this.setData({
      lon: Number(options.lon),
      lat: Number(options.lat),
      type: options.type
    })
  },
  onShow() {
    this.userAuthorize();
  },
  /**
   * 检查用户是否授权 
   */
  userAuthorize: function () {
    let _this = this;
    wx.getSetting({
      success(res) {
        _this.setData({
          cameraFlag: res.authSetting['scope.camera']
        }, () => {
          if (!_this.data.cameraFlag) {
            if (isShowTitle) {
              wx.openSetting({
                success() {
                  isShowTitle = false
                }
              })
            }
          }
        })
      },
      fail(res){
        console.log('获取授权异常',res);
      }
    })
  },
  takePhoto: function () {
    let { type, lat, lon } = this.data;
    let _this = this;
    const ctx = wx.createCameraContext()
    wx.showLoading({
      mask: true,
      title:'上传中'
    })
    console.log(ctx);
    ctx.takePhoto({
      quality: 'low',
      success: (res) => {
        console.info(res);
        console.log(res.tempImagePath);
        let file = res.tempImagePath;
        wx.uploadFile({
          filePath: file,
          name: 'file',
          url: type === "init" ? clockinInitUrl : clockinUrl,
          header: {
            'user-code': wx.getStorageSync("userCode")
          },
          formData: {
            lon,
            lat,
            bssid: ''
          },
          success: (result) => {
            console.info(result, '成功结果')
            let data = result.data;
            if (result.statusCode === 200) {
              if (typeof result.data === 'string') data = JSON.parse(data);
              if (data.state === 'success') {
                wx.navigateBack();
              } else {
                _this.errFilter(data.data);
              }
            } else {
              wx.showModal({
                title: '提示',
                content: '服务器错误',
                showCancel: false
              })
            }
          },
          complete: () => {
            wx.hideLoading();
          }
        })
      }
    })
  },
  /**
   * 错误过滤 
   */
  errFilter(data) {
    let str = null;
    switch (data) {
      case 'user-not-init':
        str = '用户没有初始化';
        break;
      case 'not-fond-face':
        str = '没有找到人脸，或找到的人脸超过1张';
        break;
      case 'log-or-lat-error':
        str = '位置获取错误';
        break;
      case 'user-not-init-face':
        str = '用户初始化了基础数据，但没有上传人脸数据';
        break;
      case 'face-dist-overstep':
        str = '人脸检查没通过';
        break;
      case 'gps-location-overstep':
        str = '坐标超出范围';
        break;
      default:
        str = '';
        break;
    }
    wx.showModal({
      title: '提示',
      content: str,
      showCancel: false
    })
  }
})