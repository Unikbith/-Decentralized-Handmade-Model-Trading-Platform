"""图片 URL 处理"""


def fix_image_url(url):
    """将 MinIO 的 HTTP 地址转换为相对路径，配合 Nginx HTTPS 代理"""
    if not url:
        return url
    for prefix in ('http://127.0.0.1:9000/goods-images/', 'http://localhost:9000/goods-images/'):
        if url.startswith(prefix):
            return '/goods-images/' + url.split('/goods-images/', 1)[1]
    return url
