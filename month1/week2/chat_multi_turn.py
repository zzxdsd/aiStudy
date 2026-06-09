import os
from openai import OpenAI

api_key = os.environ.get("DEEPSEEK_API_KEY")
if not api_key:
    print("环境变量出错")
    exit(1)
# print(f'sk:{api_key}')

client = OpenAI(
    api_key= api_key,
    base_url= "https://api.deepseek.com"
)
# print(client.models.list())
messages = []
print("开始对话(输入 quit 或 exit 退出)")
print("-" * 40)

while True:
    user_input = input('\n你：').strip()  #strip()去除首位空格、换行符，代码更健壮
    if not user_input:
        continue
    if user_input.lower() in ['quit', 'exit']:  #注意：lower()
        break

    messages.append({'role': 'user', 'content': user_input})
    req = client.chat.completions.create(
        model= 'deepseek-v4-pro',
        messages = messages,
        stream = False
    )
    reply = req.choices[0].message.content
    messages.append({'role': 'assistant', 'content': reply})

    print(f'\n回复: {reply}')
    


