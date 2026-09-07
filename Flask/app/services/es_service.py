"""Elasticsearch 商品索引同步"""
from elasticsearch.exceptions import NotFoundError

from ..extensions import es_client
from ..models import Goods
from ..utils.image import fix_image_url

GOODS_INDEX = 'goods_index'


def sync_goods_to_es(goods_id):
    """将单条商品数据同步到 ES 索引"""
    try:
        goods = Goods.query.get(goods_id)
        if not goods:
            return
        doc = {
            "name": goods.name,
            "price": float(goods.price),
            "stock": goods.stock,
            "image": fix_image_url(goods.images.split(',')[0]) if goods.images else "",
            "description": goods.description or "",
            "category": goods.category or "",
            "status": goods.status or "",
            "brand": goods.brand or "",
            "ip": goods.ip or "",
            "charactername": goods.charactername or "",
            "merchant_name": goods.merchant_name,
        }
        es_client.index(index=GOODS_INDEX, id=str(goods.id), body=doc)
    except Exception as e:
        print(f"同步商品到ES失败: {e}")


def delete_goods_from_es(goods_id):
    """从 ES 中删除商品"""
    try:
        es_client.delete(index=GOODS_INDEX, id=str(goods_id))
    except NotFoundError:
        print(f"ES中未找到商品{goods_id}")
    except Exception as e:
        print(f"删除ES商品失败: {e}")
