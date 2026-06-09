import os
import requests

api_key = os.environ.get("DEEPSEEK_API_KEY")
if not api_key:
    print("环境变量为空")
    exit(1)

url = "https://api.deepseek.com/chat/completions"

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {api_key}'
}

data = {
    'model': 'deepseek-v4-pro',
    'messages': [
        {'role': 'system', 'content': 'You are a helpful assistant'},
        {'role': 'user', 'content': 'Hello'}
    ]
}

req = requests.post(url, headers= headers, json = data)
print(f'状态码:{req.status_code}')
print(f'原始返回:{req.text}')
print('---')
print(f'完整返回:{req.json()}')
print('---')
print(f'模型回复: {req.json()['choices'][0]['message']['content']}')
