// ===== 全局环境配置 =====
// 说明：生产部署时请按实际环境修改以下域名/地址配置。

// 后端 API 接口地址：留空表示走同源请求，由部署层反向代理 /api
export const API_BASE_URL = ''

// 前端支付网关地址（用于生成扫码支付的二维码 URL）
// 注意：若非正式线上支付网关，请替换为实际可用的支付域名
export const PAY_GATEWAY_URL = 'https://pay.anime-model.com'