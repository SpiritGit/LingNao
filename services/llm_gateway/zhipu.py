from zai import ZhipuAiClient
import os

# 从环境变量读取 API Key
client = ZhipuAiClient(api_key=os.getenv("ZAI_API_KEY"))
print(os.getenv("ZAI_API_KEY"))

# Create chat completion
response = client.chat.completions.create(
    model='glm-4.7',
    messages=[
        {'role': 'system', 'content': '你是一个 AI 作家.'},
        {'role': 'user', 'content': '讲一个关于 AI 的故事.'},
    ],
    stream=True,
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='')