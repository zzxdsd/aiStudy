# README/决策说明

## README
### 1、项目介绍
- 这是一个把月 1 笔记 agent 改造成 HTTP 服务的练习项目,同时提供自然语言入口和结构化 API
    - notes_server.py：挂载在uvicorn服务器上的服务端
    - client.py：用requests库调用notes_server服务
### 2、装/跑
- pip install fastapi uvicorn
- uvicorn xxx:app --reload
### 3、端点列表
- chat_server
    - 调用llm实现对笔记的增查
    - 给llm发送一段自然语言，而调用llm的端点挂载在uvicorn服务器上，client.py需要将自然语言作为POST HTTP的请求体发送给端点。
- save_server
    - 将content和tag作为请求体内容发给uvicorn服务器，uvicorn服务器再调用FastAPI，将其作为参数传给save_server函数
- get_server
    - 查询所有笔记
- search_server
    - 根据关键词查询某条笔记
- delete_server
    - 根据笔记id删除某条笔记
### 4、调用示例
- 运行python client.py

## 决策说明
### 1、哪些用 POST、哪些用 GET、哪些用 DELETE,为什么
- chat_server和save_server用POST
    - 二者均需要创建笔记，HTTP请求中创建用POST
    - chat_server本质是"提交一次自然语言指令请求处理",处理结果可能是创建、可能是查询、模型自己决定。POST 不是因为"创建",是因为它是"提交动作让服务端做事";而 GET 严格意义上应该是"取数据、无副作用"。chat 一次调用可能写文件,所以必须 POST。
- get_server和search_server用GET
    - 查询用GET
- delete_server用DELETE
    - 删除用DELETE

### 2、Pydantic 模型为什么这么设计
- ChatRequest
    - 设计了session_id字段，代表用户id，必须要有这个参数，否则服务端分不清用户
- SaveRequest
    - content作为要保存的内容是必填项
    - tag作为标签不是必填的，因此可以为None

### 3、把 agent 嵌进 HTTP 服务时,遇到了什么问题、怎么解的
- 设计问题：如果将增删查的功能拆分到不同的端点中，还需要调用llm吗？
    - 答案是不需要
    - llm本身的作用就是理解用户语义，根据语义自主决定调用什么函数；
    - 而不同的端点意味着已经明确了用户意图，确定了该端点的功能，因此不需要调用llm再去判断用户意图————即HTTP路径替代llm来分发请求
    - LLM 是"用自然语言路由请求"的工具，路径是"用 URL 路由请求"的工具
- 多轮对话问题：HTTP 每次请求是独立的——这是不是意味着我不需要再while循环里处理多轮用户对话的情况？既然每个 HTTP 请求独立、服务器默认不认得"这是同一个用户"——那 messages 这个跨多轮对话的历史,怎么办?
    - 三个常见选择,各有取舍:
        - 每次请求重建 —— messages 不跨请求保存。用户每发一条消息,服务端从零开始 messages = [新消息],跑完丢掉。问题:模型没有上下文记忆,你说"我叫 Iris",下一条问"我叫什么",答不上
        - 客户端管历史 —— 客户端每次把完整对话历史塞进请求一起发。{"messages": [...全部历史...]}。好处:服务端无状态;坏处:每次请求负载越来越大
        - 服务端按 session 管 —— 引入 session_id,服务端用一个字典存 {session_id: messages}。客户端每次请求带上 session_id。好处:符合传统聊天体验;坏处:服务端要管内存/状态
    - 我选择3，原因是我觉得会话管理这种“管理”行为本身就更适合在服务端来做
        - 问题：这种情况下messages仍然是全局变量吧？我记得claude曾经提过全局变量在 HTTP 世界水土不服？
- 引用和拷贝混乱问题
    - 源代码中，我用get返回了messages的引用（我误以为是拷贝），在后续进行了update（实际是无用操作，因为get返回了引用后，后续操作本身就是在原列表上操作）
    - 修正：明确引用方案，删去update操作，并且处理新session导致游离列表的问题
        - session_messages = messages.get(chatRequest.session_id, []) 这行——新 session 的更新会丢失。
        - .get(key, []) 当 key 不存在时，返回的 [] 是一个全新的列表，没有放进 messages 字典里。后面你 append 操作的是这个游离的列表，messages 字典里没有这条 session。
        ```python
        if chatRequest.session_id not in messages:
            messages[chatRequest.session_id] = []
        session_messages = messages[chatRequest.session_id]
        ```
- 持久化问题
    - week2中我用全局变量messages来进行多轮对话管理，history.json来进行持久化的对话管理
    - week6中只用了一个messages全局变量（字典）来根据用户id管理多轮对话，并没有做本地持久化， messages 字典只在内存,服务重启就丢。这周已经在搭 HTTP 服务、嵌 agent、客户端联调,任务密度已满,持久化推到月 3 数据库一并解决
- id问题
    - 删除某条笔记后，其他笔记的id要不要跟着改？
        - 不要，业内通用设计
    - 后续新增笔记的id怎么办？
        - 取当前笔记内最大id+1
    - 对比着messages 那个问题想一下：
        - messages 那个用 dict + setdefault 是因为它本来就该在内存里（多轮会话状态，重启想保留是更复杂的事，这周不做）。
        - next_id 不一样,它的真相天然在 note.json 里——所有已用 id 都在文件里写着,从那里算最大值是符合直觉的。
        - 判断一个状态"该不该全局变量",问一句:它的真相归属在哪? 真相在文件/数据库里 → 别另开内存副本;真相天然就在内存(像 session 这种) → 才用变量。
