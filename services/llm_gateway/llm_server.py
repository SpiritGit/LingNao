import os
import json
from fastapi import FastAPI, Body
from fastapi.responses import StreamingResponse
from zai import ZhipuAiClient  # 确保已安装 zai-sdk

app = FastAPI(title="LingNao LLM Service")

# 初始化客户端
# 建议在终端执行: export ZAI_API_KEY='你的KEY'
client = ZhipuAiClient(api_key=os.getenv("ZAI_API_KEY"))

async def generate_chat_stream(messages, model):
    """流式生成器：供网页端使用"""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            # 按照 Server-Sent Events (SSE) 格式返回
            yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"

@app.post("/v1/chat")
async def chat(
    payload: dict = Body(...), 
    stream: bool = False
):
    """
    统一聊天接口
    payload 格式: {"model": "glm-4.7", "messages": [...]}
    """
    model = payload.get("model", "glm-4.7")
    messages = payload.get("messages", [])

    # 模式 1：流式返回 (适合 H5 网页)
    if stream:
        return StreamingResponse(
            generate_chat_stream(messages, model), 
            media_type="text/event-stream"
        )

    # 模式 2：一次性返回 (适合飞书机器人)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=False,
    )
    return {"reply": response.choices[0].message.content}

if __name__ == "__main__":
    import uvicorn
    # 监听 8001 端口，方便 Nginx 转发
    uvicorn.run(app, host="0.0.0.0", port=8001)