"""AI 客服：意图分析 + 对话 + Redis 加权商品搜索推荐"""
import json
import re
import time

import requests

from ..config import ZHIPU_API_KEY, ZHIPU_API_URL
from ..extensions import redis_client
from ..models import Goods
from ..utils.image import fix_image_url

# AI 客服商品缓存（索引放 Redis，商品对象列表缓存在进程内）
_goods_cache = {'data': None, 'updated_at': 0}
_GOODS_CACHE_TTL = 300  # 缓存有效期 5 分钟

# 各字段搜索权重
FIELD_WEIGHTS = {
    'ip': 5,             # IP 匹配权重最高
    'charactername': 5,  # 角色名匹配权重最高
    'name': 4,           # 商品名次之
    'brand': 3,          # 品牌再次
    'category': 2,       # 分类最低
}


def rebuild_redis_goods_index(goods_list):
    """将商品多字段索引写入 Redis，支持按字段加权搜索"""
    pipe = redis_client.pipeline()
    for key in redis_client.keys('ai_index:*'):
        pipe.delete(key)
    pipe.delete('ai_index:goods_map')

    goods_map = {}
    for g in goods_list:
        price = float(g.price) if g.price else 0
        goods_map[str(g.id)] = json.dumps({
            'id': g.id,
            'name': g.name or '',
            'price': price,
            'ip': g.ip or '',
            'charactername': g.charactername or '',
            'brand': g.brand or '',
            'category': g.category or '',
            'image': fix_image_url(g.images.split(',')[0]) if g.images else '',
        }, ensure_ascii=False)

        for field, weight in FIELD_WEIGHTS.items():
            val = getattr(g, field, None)
            if val and val.strip():
                redis_key = f'ai_index:field:{field}:{val.strip().lower()}'
                pipe.sadd(redis_key, g.id)
                pipe.expire(redis_key, 600)

    pipe.execute()
    redis_client.hset('ai_index:goods_map', mapping=goods_map)
    redis_client.expire('ai_index:goods_map', 600)
    print(f"[Redis索引] 已构建，共 {len(goods_list)} 个商品")


def get_cached_goods():
    """获取缓存的在售商品列表，并同步构建 Redis 索引"""
    if _goods_cache['data'] is not None and (time.time() - _goods_cache['updated_at']) < _GOODS_CACHE_TTL:
        return _goods_cache['data']
    try:
        goods_list = Goods.query.filter(Goods.status != '下架').all()
        _goods_cache['data'] = goods_list
        _goods_cache['updated_at'] = time.time()
        rebuild_redis_goods_index(goods_list)
        print(f"[商品缓存] 已更新，共 {len(goods_list)} 个商品")
    except Exception as e:
        print(f"[商品缓存] 加载失败: {e}")
        if _goods_cache['data'] is not None:
            return _goods_cache['data']
        return []
    return _goods_cache['data']


def search_by_redis_index(keywords, user_message=''):
    """使用 AI 提取的关键词在 Redis 多字段索引中加权搜索，返回最优商品"""
    try:
        if not keywords:
            return None

        # 从原始消息/关键词中提取预算
        budget_max = None
        budget_match = re.search(r'(\d+)\s*[元块]?', user_message)
        if budget_match and any(w in user_message for w in ['预算', '以内', '以下', '不超过', '只有', '就', '左右', '块钱']):
            budget_max = int(budget_match.group(1))
        for kw in keywords:
            if kw.isdigit() and int(kw) >= 10:
                budget_max = int(kw)

        all_index_keys = redis_client.keys('ai_index:field:*')
        if not all_index_keys:
            return None

        # 对每个关键词扫描所有字段索引，累计加权得分
        goods_scores = {}
        for keyword in keywords:
            kw_lower = keyword.lower()
            for redis_key in all_index_keys:
                parts = redis_key.split(':', 3)
                if len(parts) < 4:
                    continue
                field = parts[2]
                index_word = parts[3]
                if kw_lower in index_word or index_word in kw_lower:
                    weight = FIELD_WEIGHTS.get(field, 1) + min(len(kw_lower), 3)
                    for gid in redis_client.smembers(redis_key):
                        gid = int(gid)
                        goods_scores[gid] = goods_scores.get(gid, 0) + weight

        if not goods_scores:
            return None

        # 读取商品详情并应用预算过滤
        candidates = []
        for gid, score in goods_scores.items():
            raw = redis_client.hget('ai_index:goods_map', str(gid))
            if not raw:
                continue
            g = json.loads(raw)
            price = g.get('price', 0)
            if budget_max:
                if price > budget_max * 1.2:
                    score -= 20
                elif price > budget_max:
                    score -= 5
                else:
                    ratio = price / budget_max if budget_max > 0 else 0
                    score += int(5 * ratio)
            if score > 0:
                candidates.append((g, score))

        if not candidates:
            for gid, score in goods_scores.items():
                raw = redis_client.hget('ai_index:goods_map', str(gid))
                if raw:
                    candidates.append((json.loads(raw), score))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[1], reverse=True)
        best = candidates[0][0]
        print(f"[Redis搜索] 关键词:{keywords} → 匹配商品: {best['name']}, 分数: {candidates[0][1]}")
        return best
    except Exception as e:
        print(f"[Redis搜索] 异常: {e}")
        return None


def get_fallback_reply(message):
    """AI 服务不可用时的预设回复"""
    if not message:
        return "您好，请问有什么可以帮您？"
    message = message.lower()
    if '订单' in message or '发货' in message:
        return '关于订单问题，您可以在"我的订单"中查看详情。如有其他问题，请详细描述，我们会尽快处理。'
    if '退款' in message or '退货' in message:
        return '退款/退货申请请在订单详情中提交售后申请，商家会在1-3个工作日内处理。'
    if '商品' in message or '手办' in message:
        return '关于商品问题，您可以在商品详情页查看更多信息，或直接联系商家咨询。'
    if '支付' in message:
        return '支付问题请联系客服或在工作时间咨询。'
    if '收藏' in message:
        return '您可以在商品详情页点击收藏按钮，收藏的商品在个人中心的"我的收藏"中查看。'
    return '感谢您的咨询，我们会尽快为您处理！'


def handle_chat(data):
    """处理 AI 客服请求，返回 (reply, goods, error_msg)"""
    if not data:
        return None, None, '消息不能为空'
    user_message = data.get('message', '')
    conversation_history = data.get('history', [])
    if not user_message:
        return None, None, '消息不能为空'

    try:
        # 确保商品缓存和 Redis 索引可用
        get_cached_goods()

        system_prompt = """你是次元模仓AI客服，负责手办、模型咨询。
你需要判断用户意图并回复。

【意图判断规则】
- 如果用户有购买/寻找商品的意图（如：想买、推荐、有没有、找、看看、想要、需要等），判定为"purchase"
- 如果用户只是闲聊/问订单/问售后等，判定为"chat"

【回复格式】
第一行输出意图标记，第二行开始是回复内容：
purchase:关键词1,关键词2,关键词3
回复内容...

chat
回复内容

示例：
purchase:初音未来,200
为您找到了初音相关的手办，请看推荐~

chat
关于订单问题，请在"我的订单"中查看。"""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history[-5:])
        messages.append({"role": "user", "content": user_message})

        chat_payload = {
            "model": "glm-4.5-air",
            "messages": messages,
            "max_tokens": 150,
            "temperature": 0.6,
        }

        headers = {"Authorization": f"Bearer {ZHIPU_API_KEY}", "Content-Type": "application/json"}
        response = None
        for attempt in range(2):
            try:
                response = requests.post(ZHIPU_API_URL, headers=headers, json=chat_payload, timeout=20)
                break
            except (requests.exceptions.ReadTimeout, requests.exceptions.Timeout) as e:
                print(f"[AI重试] 第{attempt + 1}次超时: {e}")

        goods_data = None
        if response and response.status_code == 200:
            result = response.json()
            raw_reply = result['choices'][0]['message']['content']
            print(f"[AI原始回复] {raw_reply}")

            lines = raw_reply.strip().split('\n', 1)
            first_line = lines[0].strip()
            reply_body = lines[1].strip() if len(lines) > 1 else first_line

            if first_line.lower().startswith('purchase:'):
                keywords = [k.strip() for k in first_line[len('purchase:'):].split(',') if k.strip()]
                print(f"[意图分析] 购买意图，关键词: {keywords}")
                goods_data = search_by_redis_index(keywords, user_message)
                ai_reply = re.sub(r'\[RECOMMEND:\d+\]', '', reply_body).strip()
                ai_reply = re.sub(r'商品[ID编号：:]*\d+', '', ai_reply).strip()
            elif first_line.lower() == 'chat':
                ai_reply = reply_body
                print("[意图分析] 普通对话")
            else:
                ai_reply = raw_reply
                print("[意图分析] 解析失败，使用原始回复")
        else:
            print(f"智谱AI调用失败: {response.status_code if response else '无响应'}")
            ai_reply = get_fallback_reply(user_message)

        return ai_reply or get_fallback_reply(user_message), goods_data, None
    except Exception as e:
        print(f"AI客服错误: {e}")
        return get_fallback_reply(user_message), None, None
