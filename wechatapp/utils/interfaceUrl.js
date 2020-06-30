const netUrl = "https://api.clockin.vaccine.pub";
// 获取用户信息
const getUserInfoUrl = `${netUrl}/status`;

// 初始化打卡
const clockinInitUrl = `${netUrl}/init`;

// 打卡地址
const clockinUrl = `${netUrl}/clock`;

module.exports = {
  getUserInfoUrl,
  clockinInitUrl,
  clockinUrl
}