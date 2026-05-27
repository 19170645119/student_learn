# 🎓 个性化学习平台 (Personalized Learning Platform)
我修改这试一下，学习操作

基于 AI 的个性化学习系统，支持学习画像构建、智能资源生成、知识路径规划。

---

## 🏗️ 技术栈

| 层 | 技术 |
|---|------|
| 后端框架 | FastAPI (Python 3.13) |
| 数据库 | MySQL 8.0 + SQLAlchemy Async |
| AI 模型 | 讯飞星火 spark-x（画像）/ 阿里百炼 qwen-max（资源中心） |
| 前端 | Vue 3 + Vite |
| Markdown | marked |
| 图表 | Mermaid |

---

## 📁 项目结构

```
student_learn/
├── backend/
│   ├── core/agents/     # AI Agent（画像/文档/对话/路径）
│   ├── models/          # ORM 模型
│   ├── repository/      # 数据访问层
│   ├── routers/         # API 路由
│   ├── schemas/         # Pydantic 模型
│   ├── settings/        # 配置
│   └── main.py          # 入口
├── frontend/
│   ├── src/views/       # 页面组件
│   ├── src/http/        # API 封装
│   └── src/router/      # 路由
└── .env.example         # 环境变量模板
```

---

## 📦 依赖安装

| 位置 | 命令 | 说明 |
|------|------|------|
| `backend/requirements.txt` | `pip install -r requirements.txt` | Python 后端（11 个包） |
| `frontend/package.json` | `npm install` | Vue/Vite/marked/mermaid |

---

## 🚀 快速开始

## 🖥️ 需要安装的软件

| 软件 | 最低版本 | 必须 | 下载地址 |
|------|----------|------|----------|
| Python | 3.13+ | ✅ 是 | https://www.python.org/downloads/ |
| Node.js | 18+ | ✅ 是 | https://nodejs.org/ |
| MySQL | 8.0+ | ✅ 是 | https://dev.mysql.com/downloads/ |
| Redis | 6.0+ | ❌ 可选 | https://redis.io/download/ |
| Git | 任意 | ✅ 是 | https://git-scm.com/ |

### Python 安装后验证
```bash
python --version   # 应显示 3.13.x
pip --version      # 确认 pip 可用
```

### Node.js 安装后验证
```bash
node --version     # 应显示 18.x 或更高
npm --version      # 确认 npm 可用
```

### MySQL 安装后配置
1. 安装时设置 root 密码
2. 创建数据库：
```sql
CREATE DATABASE student_learn CHARACTER SET utf8mb4;
```

### 推荐工具
| 工具 | 用途 | 下载 |
|------|------|------|
| Navicat Premium Lite 17 | MySQL 可视化管理（免费版） | https://www.navicat.com/en/download/navicat-premium-lite |
| Tiny RDM | Redis 桌面管理器（轻量免费） | https://redis.tinycraft.cc/ |
| GitHub Desktop | Git 图形化管理 / 推送代码 | https://desktop.github.com/ |

### Redis（可选）
- 学习路径功能用到，不装也能运行其他功能
- Windows 用户可从 https://github.com/tporadowski/redis/releases 下载

---

## 🚀 快速开始

### 1. 环境准备

### 2. 创建数据库

```sql
CREATE DATABASE student_learn CHARACTER SET utf8mb4;
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key 和数据库密码
```

### 4. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

---

## 🔑 需要申请的 API

| 服务 | 用途 | 申请地址 |
|------|------|----------|
| 讯飞星火 spark-x | 学习画像对话 | https://console.xfyun.cn/ |
| 阿里百炼 qwen-max | 文档生成 + 资源对话 | https://bailian.console.aliyun.com/ |
| QQ邮箱 SMTP | 注册验证码 | QQ邮箱 → 设置 → 账户 → POP3/SMTP |

### API 配置位置

| 模型 | 配置文件 |
|------|----------|
| spark-x | `.env` 中 `LLM_API_KEY`，代码 `backend/core/spark_service.py` |
| qwen-max | `.env` 中 `DASHSCOPE_API_KEY`，代码 `backend/core/openai_service.py` |

---

## 📡 API 端点

### 认证
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/login` | 登录 |
| POST | `/auth/register` | 注册 |
| GET | `/auth/code` | 获取邮箱验证码 |

### 学习画像
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/profile/` | 获取画像 |
| PUT | `/profile/` | 更新画像 |
| POST | `/profile/chat` | 画像构建对话 |

### 资源中心
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/resource/chat` | 智能对话（意图分析+推荐） |
| POST | `/resource/generate` | 生成课程文档 |
| POST | `/resource/generate/stream` | 流式生成文档（SSE） |
| GET | `/resource/chapters/list` | 知识章节列表 |
| GET/POST/DELETE | `/resource/sessions` | 会话管理 |

### 学习路径
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/learning-path/` | 获取学习路径 |
| POST | `/learning-path/generate` | 生成学习路径 |

---

## ⚠️ 安全提示

1. **`.env` 已加入 `.gitignore`**，不会提交到 Git
2. 使用 `.env.example` 作为模板分享给其他人
3. 如果敏感信息曾提交到 Git，建议重置相关 API Key