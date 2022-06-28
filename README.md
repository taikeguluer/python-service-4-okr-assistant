# OKR助理 —— 以OKR制定/跟踪/评价为核心的团队管理工具
- 原文链接： [https://github.com/taikeguluer/python-service-4-okr-assistant/blob/master/README.md](https://github.com/taikeguluer/python-service-4-okr-assistant/blob/master/README.md)
- 库链接： 
  - 前端（飞书小程序）：[https://github.com/taikeguluer/feishu-microapp-4-okr-assistant](https://github.com/taikeguluer/feishu-microapp-4-okr-assistant)
  - 后端（Python）：[https://github.com/taikeguluer/python-service-4-okr-assistant](https://github.com/taikeguluer/python-service-4-okr-assistant)
## 背景
`OKR助理`是帮助团队管理者落实OKR管理的工具。它自动化使用`飞书`的云文档、任务、日程、群组、文本消息、卡片消息功能，提供`飞阅会`方法、`销项管理`方法、`1on1会议`方法、团队`个人职业发展规划`的模板和实践，从而完成OKR制定、周/月/季/半年/年跟踪和评价、个人职业规划制定、核心团队定期1on1沟通、日常工作销项，最终帮助团队负责人赋能团队向着一致的目标高效前进。 

它是`飞书OKR`工具的补充，`飞书OKR`更着重OKR的制定（公开、对齐），`OKR助理`更着重OKR作为体系的有效性。

*P.S. `飞书汇报`工具更偏重传统的团队管理，目前与OKR的结合较少。*
## 业务流程
![bizflow4okrassistant](https://raw.githubusercontent.com/taikeguluer/python-service-4-okr-assistant/master/pic4readme/biz-of-okr-assistant.png)
## 技术架构
![techarch4okrassistant](https://raw.githubusercontent.com/taikeguluer/python-service-4-okr-assistant/master/pic4readme/tech-of-okr-assistant.png)
## 部署架构
### 后端服务
- 使用Docker Desktop运行后端服务
```shell
mac:~ songxiang$ docker ps
CONTAINER ID   IMAGE                          COMMAND                  CREATED      STATUS              PORTS                                                                    NAMES
ea121c4783ac   okr_assistant_service:latest   "celery -A oas.manag…"   7 days ago   Up About a minute                                                                            python-service-4-okr-assistant_oas_worker_2
710255cfe23a   okr_assistant_service:latest   "celery -A oas.manag…"   7 days ago   Up About a minute                                                                            python-service-4-okr-assistant_oas_worker_1
b2ff5b0fe0b8   nginx:latest                   "/docker-entrypoint.…"   7 days ago   Up About a minute   0.0.0.0:3001->80/tcp                                                     oas_nginx
e4cc03c1f55c   okr_assistant_service:latest   "python app.py"          7 days ago   Up About a minute                                                                            python-service-4-okr-assistant_oas_server_2
298d1cc7e5e5   okr_assistant_service:latest   "python app.py"          7 days ago   Up About a minute                                                                            python-service-4-okr-assistant_oas_server_1
2b102d878e0c   okr_assistant_service:latest   "celery -A oas.manag…"   7 days ago   Up About a minute                                                                            oas_beat
def071ffe39c   redis:latest                   "docker-entrypoint.s…"   7 days ago   Up About a minute   0.0.0.0:6379->6379/tcp                                                   oas_redis
93faef05756f   rabbitmq:latest                "docker-entrypoint.s…"   7 days ago   Up About a minute   4369/tcp, 5671/tcp, 15691-15692/tcp, 25672/tcp, 0.0.0.0:5672->5672/tcp   oas_rabbitmq
33e7e46f1241   mysql:latest                   "docker-entrypoint.s…"   7 days ago   Up About a minute   0.0.0.0:3306->3306/tcp, 33060/tcp                                        oas_mysql
```
- 使用内网穿透工具ngrok将后端服务开放到公网
```shell
mac:~ songxiang$ ps 677
  PID   TT  STAT      TIME COMMAND
  677 s001  S+    15:14.43 ngrok http 3001
```
### 前端应用
前端发布至飞书小程序运行环境。

## 快速开始
### 准备工作
#### 创建飞书企业自建应用
- 在 [飞书开发者后台](https://open.feishu.cn/app) 中创建`企业自建应用`
- 在应用配置页面的`事件订阅`中，配置`Encrypt Key`
- 在应用配置页面的`权限管理`中，获取如下权限：
  - 以应用身份读取通讯录（免审权限）
  - 获取部门基础信息（免审权限）
  - 获取部门组织架构信息（免审权限）
  - 获取用户基本信息（免审权限）
  - 获取用户组织架构信息（免审权限）
  - 获取用户雇佣信息（免审权限）
  - 获取用户user ID（免审权限）
  - 接收群聊中@机器人消息事件（免审权限）
  - 读取用户发给机器人的单聊消息（免审权限）
  - 以应用的身份发消息（免审权限）
  - 获取企业信息（免审权限）
  - 查看、评论、编辑和管理云空间中所有文件
  - 获取与更新群组信息
  - 获取与发送单聊、群组消息
#### 创建腾讯云免费对话机器人
- 在 [腾讯智能对话平台](https://console.cloud.tencent.com/tbp/bots) 上创建免费对话机器人
- 在对话机器人配置页面，打开闲聊功能
#### 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/) 、 [ngrok](https://ngrok.com/) 和 [飞书开发者工具](https://open.feishu.cn/document/uYjL24iN/ucDOzYjL3gzM24yN4MjN?lang=zh-CN)
### 后端服务
#### 获取源代码
```powershell
PS C:\> git clone git@gitlab.cicconline.com:songxiang/python-service-4-okr-assistant.git
Cloning into 'python-service-4-okr-assistant'...
remote: Enumerating objects: 53, done.
remote: Counting objects: 100% (53/53), done.
remote: Compressing objects: 100% (35/35), done.
remote: Total 77 (delta 21), reused 45 (delta 16), pack-reused 24
Receiving objects: 100% (77/77), 114.29 KiB | 653.00 KiB/s, done.
Resolving deltas: 100% (21/21), done.
PS C:\> cd .\python-service-4-okr-assistant\
```
#### 配置环境变量文件
编辑`.env`
- **APP_ID**：在飞书应用配置的凭证与基础信息页面，获取`App ID`
- **APP_SECRET**：在飞书应用配置的凭证与基础信息页面，获取`App Secret`
- **VERIFICATION_TOKEN**：在飞书应用配置的事件订阅页面，获取`Verification Token`
- **ENCRYPT_KEY**：在飞书应用配置的事件订阅页面，获取`Encrypt Key`
- **TENCENT_CLOUD_AI_BOTID**：在腾讯智能对话平台的Bot配置页面，获取`BotId`
- **TENCENT_CLOUD_API_SECRETID**：在 [腾讯云访问密匙](https://console.cloud.tencent.com/cam/capi) 页面，获取`SecretId`
- **TENCENT_CLOUD_API_SECRETKEY**：在 [腾讯云访问密匙](https://console.cloud.tencent.com/cam/capi) 页面，获取`SecretKey`
- **SQLALCHEMY_DATABASE_URI**：mysql+pymysql://root:`数据库密码`@mysql:3306/okr_assistant
#### 编译和启动后端服务
```powershell
PS C:\python-service-4-okr-assistant> .\exec.ps1
```
#### 使用ngrok将后端服务发布到公网
```powershell
PS C:\python-service-4-okr-assistant> ngrok http 3001
```
### 前端应用

#### 获取源代码
```powershell
PS C:\> git clone git@gitlab.cicconline.com:songxiang/feishu-microapp-4-okr-assistant.git
Cloning into 'feishu-microapp-4-okr-assistant'...
remote: Enumerating objects: 14, done.
remote: Counting objects: 100% (14/14), done.
remote: Compressing objects: 100% (14/14), done.
Receiving objects:  92% (99/107)sed 0 (delta 0), pack-reused 93Receiving objects:  88% (95/107)
Receiving objects: 100% (107/107), 52.45 KiB | 1.69 MiB/s, done.
Resolving deltas: 100% (32/32), done.
PS C:\> cd .\feishu-microapp-4-okr-assistant\
```
#### 配置飞书机器人
- 进入`飞书开放平台`->`开发者后台`，在应用配置页面的`事件订阅`页面，配置请求网址URL为用ngrok发布的后端服务公网地址，例如`https://1cb8-223-72-47-65.ngrok.io`
- 在应用配置页面的`应用功能`的`小程序`和`机器人`页面，打开对应功能
#### 编译发布飞书小程序
- 用`飞书开发者工具`打开源代码路径
- 在`project.config.json`中，将`appid`改为在飞书应用配置的凭证与基础信息页面获取的`App ID`
- 在`app.js`中，将`appId`改为在飞书应用配置的凭证与基础信息页面获取的`App ID`
- 在`app.js`中，将`backendService`改为用ngrok发布的后端服务公网地址（保留后面`/api/v1`），例如`https://1cb8-223-72-47-65.ngrok.io`
- 使用`上传`功能上传小程序包
- 在飞书应用配置的`应用发布`页面中，创建应用办法并发布，联系飞书管理员审核上线
### 功能验证
- 飞书机器人与应用同名，可以通过飞书全局搜索找到，可以先给它发给消息，看看AI会回复啥，不过刚开始的时候，这机器人很蠢，说的多了，会好一些
- 飞书小程序可以在飞书工作台上找到，也可以通过飞书全局搜索得到
## OKR助理使用的模板
- [OKR制定模板](https://rbnqidugqp.feishu.cn/sheets/shtcnbfHAWqOlIekBBs1ol9ReLc) ，有了付费的飞书OKR工具，这个模板就不需要了
- [OKR周报模板](https://rbnqidugqp.feishu.cn/docx/doxcnSHfULJhNmAJFxPndkuB9CO) ，可以将飞书OKR直接插入这个模板，代替其中的表格
- [OKR月/季/半年/年报模板](https://rbnqidugqp.feishu.cn/docx/doxcnGoilEOWvvco3P5fqCj5N0f) ，可以将飞书OKR直接插入这个模板，代替其中的表格
- [个人职业发展画布模板](https://rbnqidugqp.feishu.cn/docx/doxcnDcr4lz4g7fKK928325z4hc)
- [360考核调研表模板](https://rbnqidugqp.feishu.cn/sheets/shtcnOJiUF5N7LmGyZhxnR5Ghke)
- [360考核汇总表模板](https://rbnqidugqp.feishu.cn/sheets/shtcngsVGl3V2zoZ1OIxh4v4gnf)
- [月度技术专家评选模板](https://rbnqidugqp.feishu.cn/sheets/shtcn5rCLuqK7Vvln49yuEpn6Ng)
- [团队核心任职资格模板](https://rbnqidugqp.feishu.cn/file/boxcnjuXSZx1fd1Azrn2wgOLcRq)
- [团队岗位任职资格模板](https://rbnqidugqp.feishu.cn/sheets/shtcncMbUsezt1TwkeeN8GH2luh)