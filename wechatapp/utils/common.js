const {userLoginUrl} = require('./interfaceUrl');

//网络请求方法 返回一个promise
const wxRequest = (url, method = "GET", data = {},isReset) => {
  const requirtSelf = () => new Promise((resolve, reject) => {
    wx.request({
      url,
      method: method.toUpperCase(),
      header: {
        'content-type': 'application/x-www-form-urlencoded',
        'user-code': data['userCode']
      },
      data,
      success(res) {
        console.info(res)
        resolve(res);
      },
      fail(err) {
        wx.showToast({
          icon: "none",
          title: "接口错误"
        });
        reject(err);
      }
    })
  });
  return new Promise((resolve, reject) => {
    requirtSelf().then(res => {
      if (!res.data.success && isReset) {
        
      } else {
        resolve(res)
      }
    }).catch(err => {
      reject(err)
    })
  });
};

module.exports = {
  wxRequest
}