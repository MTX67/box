from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
import hmac
import hashlib
import json
import time
from datetime import datetime

app = FastAPI()

# ========== 替换为你的凭证 ==========
import os
APP_ID = os.environ.get("APP_ID", "1905191765")
APP_SECRET = os.environ.get("APP_SECRET", "")

# ===================================
user_weights = {} 
def verify_signature(body: bytes, signature: str, timestamp: str) -> bool:
    message = timestamp.encode() + body
    expected = hmac.new(
        APP_SECRET.encode(),
        message,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.post("/")
async def handle(
    request: Request,
    x_signature: str = Header(None, alias="X-Signature-Ed25519"),
    x_timestamp: str = Header(None, alias="X-Signature-Timestamp")
):
    body = await request.body()
    data = json.loads(body)
    print(f"收到: {data}")
    
    if data.get("t") == "MESSAGE_CREATE":
        msg_data = data.get("d", {})
        content = msg_data.get("content", "")
        
        reply = None
        
        if "你好" in content or "hello" in content.lower():
            reply = "你好呀！我是 Roller-I🤖"
        elif "几点" in content or "时间" in content:
            reply = f"现在是 {datetime.now().strftime('%H:%M:%S')}"
        elif "帮助" in content or "help" in content:
            reply = "我会回复：你好、几点了、帮助"
        elif "滚" in content:
            reply = "😢 好吧..."
        else:
            reply = f"你说了：{content}\n输入「帮助」查看我能做什么"
        elif "随机" in content or "抽数字" in content or "roll" in content.lower():
            import random
            import re
            
            numbers = re.findall(r'\d+', content)
            
            if len(numbers) >= 2:
                start, end = int(numbers[0]), int(numbers[1])
                if start > end:
                    start, end = end, start
            elif len(numbers) == 1:
                start, end = 1, int(numbers[0])
            else:
                start, end = 1, 100
            
            result = random.randint(start, end)
            reply = f"🎲 随机结果：{result}\n范围：{start} ~ {end}"
        # =====================================
        
        else:
            reply = f"你说了：{content}\n输入「帮助」查看我能做什么"

        if reply:
            return {"content": reply, "msg_type": 0}
            
        elif "加权随机" in content or "pro-roll" in content.lower() or "proroll" in content.lower():
            import random
            import re
            
            user_id = msg_data.get("author", {}).get("id", "default")
            numbers = re.findall(r'\d+', content)
            weights = user_weights.get(user_id, {})
            
            # 确定范围
            if len(numbers) >= 2:
                start, end = int(numbers[0]), int(numbers[1])
                if start > end:
                    start, end = end, start
            elif len(numbers) == 1:
                start, end = 1, int(numbers[0])
            else:
                start, end = 1, 100
            
            # 构建加权列表
            weighted_list = []
            for num in range(start, end + 1):
                w = weights.get(num, 1)
                if w > 0:
                    weighted_list.extend([num] * w)
            
            if not weighted_list:
                reply = "范围内没有可抽取的数字～"
            else:
                result = random.choice(weighted_list)
                total = len(weighted_list)
                result_weight = weights.get(result, 1)
                prob = (result_weight / total) * 100
                
                reply = f"🎲 加权随机结果：{result}\n范围：{start} ~ {end}\n概率：{prob:.1f}%"
                
                # 如果有自定义权重，显示出来
                custom = {k: v for k, v in weights.items() if start <= k <= end and v != 1}
                if custom:
                    lines = ["\n📊 自定义权重："]
                    for num in sorted(custom.keys()):
                        w = custom[num]
                        p = (w / total) * 100
                        lines.append(f"  {num}: 权重{w} ({p:.1f}%)")
                    reply += "\n" + "\n".join(lines)
        
        # ========== 设置权重 ==========
        elif content.startswith("权重") or content.startswith("概率"):
            import re
            match = re.match(r'(?:权重|概率)\s*(\d+)\s*[=:：]\s*(\d+)', content)
            if match:
                num = int(match.group(1))
                weight = int(match.group(2))
                user_id = msg_data.get("author", {}).get("id", "default")
                
                if user_id not in user_weights:
                    user_weights[user_id] = {}
                
                if weight <= 0:
                    if num in user_weights[user_id]:
                        del user_weights[user_id][num]
                    reply = f"✅ 已恢复 {num} 为默认权重（1）"
                else:
                    user_weights[user_id][num] = weight
                    reply = f"✅ 已设置：数字 {num} 的权重 = {weight}"
            else:
                reply = "格式：权重 5=10\n（数字=权重，权重≥1）"
        
        # ========== 查看/清除权重 ==========
        elif content == "查看权重":
            user_id = msg_data.get("author", {}).get("id", "default")
            weights = user_weights.get(user_id, {})
            if not weights:
                reply = "还没有设置权重～\n用「权重 5=10」来设置"
            else:
                lines = ["📊 权重设置："]
                for num in sorted(weights.keys()):
                    lines.append(f"  {num} → 权重 {weights[num]}")
                reply = "\n".join(lines)
        
        elif content == "清除权重":
            user_id = msg_data.get("author", {}).get("id", "default")
            if user_id in user_weights:
                user_weights[user_id] = {}
            reply = "✅ 已清除所有权重"

    elif data.get("t") == "READY":
        print("连接成功！")
        return {}
    
    return {}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
