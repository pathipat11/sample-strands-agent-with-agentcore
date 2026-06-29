# Local Development Guide — Strands Agent Chatbot

คู่มือสำหรับรันโปรเจ็คนี้บนเครื่อง local โดยไม่ต้อง deploy AWS infrastructure (Terraform)  
ใช้ได้ทั้ง Windows, macOS, Linux

---

## เครื่องมือและ Services ทั้งหมดที่โปรเจ็คนี้ใช้

### Frameworks & SDKs (โค้ด)

| เครื่องมือ | หน้าที่ | ใช้ตรงไหน |
|-----------|--------|----------|
| **Strands Agents SDK** | Python framework สำหรับสร้าง AI agent (tool orchestration, multi-turn) | Backend ทั้งหมด |
| **FastAPI** | Web framework (Python) สำหรับ API server | Backend entry point (`main.py`) |
| **Next.js 16** | React framework สำหรับ frontend + BFF (Backend-for-Frontend) | Frontend ทั้งหมด |
| **AG-UI Protocol** | มาตรฐาน streaming agent → UI | ส่ง events จาก agent กลับมาหา frontend |
| **A2A Protocol** | Agent-to-Agent communication protocol | Agent คุยกันระหว่าง containers |
| **MCP (Model Context Protocol)** | มาตรฐานเชื่อมต่อ tools | Gateway tools เรียกผ่าน MCP |
| **AWS Amplify SDK** | Auth library (frontend) | Cognito login/signup |

### AWS Services (Cloud)

| Service | หน้าที่ในโปรเจ็ค | ต้อง deploy? |
|---------|-----------------|-------------|
| **Amazon Bedrock** | เรียก LLM models (Claude, Nova, DeepSeek ฯลฯ) | ❌ ไม่ต้อง deploy, ใช้ API ตรงได้เลยถ้ามี credentials |
| **AgentCore Runtime** | Managed container สำหรับรัน agent | ✅ ต้อง deploy (ใช้ local Python แทนได้) |
| **AgentCore Memory** | Persistent conversation + long-term summarization | ✅ ต้อง deploy (ใช้ local file แทนได้) |
| **AgentCore Gateway** | MCP tool server + JWT auth → Lambda tools | ✅ ต้อง deploy |
| **AgentCore Code Interpreter** | Sandboxed Python/JS execution | ✅ ต้อง deploy |
| **AgentCore Browser** | Headless browser + live view | ✅ ต้อง deploy |
| **Amazon Nova Act** | Visual AI model สำหรับ browser automation | ✅ ต้อง deploy + workflow definition |
| **Amazon Nova Sonic 2** | Real-time voice model (bidirectional) | ✅ ต้อง deploy (Runtime WebSocket) |
| **Amazon Cognito** | User authentication (signup/login/JWT) | ✅ ต้อง deploy (ใช้ anonymous แทนได้) |
| **Amazon DynamoDB** | Session storage + user preferences | ✅ ต้อง deploy (ใช้ local file แทนได้) |
| **Amazon S3** | Artifact/file storage (workspace) | ✅ ต้อง deploy (ใช้ local file แทนได้) |
| **AWS Lambda** | Gateway tool execution (Wikipedia, Finance ฯลฯ) | ✅ ต้อง deploy |
| **Amazon ECR** | Container registry (store Docker images) | ✅ ต้อง deploy (cloud deployment only) |
| **Amazon ECS Fargate** | Run frontend + backend containers | ✅ ต้อง deploy (cloud deployment only) |
| **Amazon CloudFront** | CDN + routing | ✅ ต้อง deploy (cloud deployment only) |
| **AWS SSM Parameter Store** | Config storage (IDs, secrets) | ✅ ต้อง deploy (ใช้ env var แทนได้) |
| **AWS Secrets Manager** | API keys (Tavily, Google, Nova Act) | ✅ ต้อง deploy (ใช้ env var แทนได้) |

### Infrastructure Tools

| เครื่องมือ | หน้าที่ | ต้องใช้ตอนไหน |
|-----------|--------|--------------|
| **Terraform** (≥1.11) | Infrastructure-as-Code สำหรับ deploy ทุก AWS resource | เฉพาะตอน deploy ขึ้น cloud |
| **Docker** | Build container images สำหรับ Runtime/Frontend | เฉพาะตอน deploy ขึ้น cloud |
| **AWS CodeBuild** | CI/CD build containers | เฉพาะ cloud (Terraform จัดการ) |

### External APIs (3rd Party)

| API | ใช้ทำอะไร | ต้องมี Key? | ฟรี? |
|-----|----------|------------|------|
| **DuckDuckGo** | Web search | ไม่ต้อง | ฟรี |
| **Open-Meteo** | Weather data | ไม่ต้อง | ฟรี |
| **Wikipedia API** | Wikipedia search | ไม่ต้อง | ฟรี |
| **ArXiv API** | Academic paper search | ไม่ต้อง | ฟรี |
| **Yahoo Finance** | Stock/financial data | ไม่ต้อง | ฟรี |
| **Google Custom Search** | Web search (premium) | ต้อง | Free tier มี |
| **Google Maps** | Location/maps | ต้อง | Free tier มี |
| **Tavily** | AI-optimized search | ต้อง | 1000 req/เดือนฟรี |

---

## Prerequisites (ต้องมีก่อนเริ่ม)

| รายการ | Version ขั้นต่ำ | หมายเหตุ |
|--------|----------------|----------|
| Python | 3.13+ | ใช้ `py -0` (Windows) หรือ `python3 --version` เช็ค |
| Node.js | 18+ | https://nodejs.org (LTS recommended) |
| AWS CLI | 2.x | `aws --version` เช็ค |
| AWS Account | — | ต้องเปิด **Bedrock model access** สำหรับ Amazon Nova Pro |

### เช็ค Bedrock Access

```bash
aws bedrock list-foundation-models --region us-east-1 \
  --query "modelSummaries[?contains(modelId,'nova')].[modelId]" --output text
```

ถ้าเห็น `amazon.nova-pro-v1:0` แสดงว่าใช้ได้ ถ้าไม่เจอ → ไปเปิดที่ AWS Console > Bedrock > Model access

---

## Step 1: Clone โปรเจ็ค

```bash
git clone https://github.com/aws-samples/sample-strands-agent-with-agentcore.git
cd sample-strands-agent-with-agentcore
```

---

## Step 2: แก้ไขไฟล์ (เปลี่ยน Model เป็น Nova Pro)

โปรเจ็คนี้ default ใช้ Claude ซึ่งต้อง enable แยก — ถ้าจะใช้ Nova Pro แทน ต้องแก้ไฟล์ต่อไปนี้:

### 2.1 Backend — เปลี่ยน Default Model

**ไฟล์:** `chatbot-app/agentcore/src/agent/config/constants.py`
```python
# บรรทัด 42 — เปลี่ยนจาก:
DEFAULT_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
# เป็น:
DEFAULT_MODEL_ID = "us.amazon.nova-pro-v1:0"
```

**ไฟล์:** `chatbot-app/agentcore/src/agents/base.py`
```python
# ใน function _get_default_model_id() — เปลี่ยน return จาก:
return "us.anthropic.claude-haiku-4-5-20251001-v1:0"
# เป็น:
return "us.amazon.nova-pro-v1:0"
```

**ไฟล์:** `chatbot-app/agentcore/src/agents/workflow_agent.py`
```python
# ใน function _get_default_model_id() — เปลี่ยน return จาก:
return "us.anthropic.claude-sonnet-4-6"
# เป็น:
return "us.amazon.nova-pro-v1:0"
```

**ไฟล์:** `chatbot-app/agentcore/src/workflows/composer_workflow.py`
```python
# บรรทัดประมาณ 263 — เปลี่ยนจาก:
self.model_id = model_id or "us.anthropic.claude-sonnet-4-6"
# เป็น:
self.model_id = model_id or "us.amazon.nova-pro-v1:0"
```

### 2.2 Backend — ลด max_tokens (Nova Pro limit = 10000)

**ไฟล์:** `chatbot-app/agentcore/src/agents/model_factory.py`
```python
# บรรทัดประมาณ 189 — เปลี่ยนจาก:
max_tokens: int = 32000,
# เป็น:
max_tokens: int = 5000,
```

**ไฟล์:** `chatbot-app/agentcore/src/agents/chat_agent.py`
```python
# ค้นหา max_tokens=32000 แล้วเปลี่ยนเป็น:
max_tokens=5000,
```

### 2.3 Frontend — เพิ่ม Nova เป็นตัวเลือก

**ไฟล์:** `chatbot-app/frontend/src/app/api/model/available-models/route.ts`

เพิ่ม Nova models ไว้ด้านบนสุดของ array `AVAILABLE_MODELS`:
```typescript
const AVAILABLE_MODELS = [
  // Amazon Nova - native Bedrock
  {
    id: 'us.amazon.nova-pro-v1:0',
    name: 'Nova Pro',
    provider: 'Amazon',
    description: 'High-capability model, balanced cost and performance'
  },
  {
    id: 'us.amazon.nova-lite-v1:0',
    name: 'Nova Lite',
    provider: 'Amazon',
    description: 'Fast and cost-effective for simpler tasks'
  },
  {
    id: 'us.amazon.nova-micro-v1:0',
    name: 'Nova Micro',
    provider: 'Amazon',
    description: 'Text-only, lowest latency and cost'
  },
  // ... (Claude และ models อื่นๆ ตามเดิม)
]
```

### 2.4 Frontend — เปลี่ยน Default Model

**ไฟล์:** `chatbot-app/frontend/src/hooks/useChat.ts`
```typescript
// ค้นหา lastModel: 'us.anthropic.claude-sonnet-4-6'
// เปลี่ยนเป็น:
lastModel: 'us.amazon.nova-pro-v1:0',
```

**ไฟล์:** `chatbot-app/frontend/src/app/api/stream/chat/route.ts`
```typescript
// ค้นหา: const defaultModelId = model_id || 'us.anthropic.claude-sonnet-4-6'
// เปลี่ยนเป็น:
const defaultModelId = model_id || 'us.amazon.nova-pro-v1:0'
```

**ไฟล์:** `chatbot-app/frontend/src/app/api/model/config/route.ts`
```typescript
// ค้นหา: model_id: 'us.anthropic.claude-sonnet-4-6'
// เปลี่ยนเป็น:
model_id: 'us.amazon.nova-pro-v1:0',
```

### 2.5 Frontend — ปิด Warmup Warning (optional)

**ไฟล์:** `chatbot-app/frontend/src/config/session.ts`

เพิ่มบรรทัดนี้ที่ต้นของ function `triggerWarmup`:
```typescript
export async function triggerWarmup(...) {
  // เพิ่มบรรทัดนี้:
  if (process.env.NEXT_PUBLIC_AGENTCORE_LOCAL === 'true') {
    return
  }
  // ... โค้ดเดิม
}
```

---

## Step 3: สร้างไฟล์ Environment

### `chatbot-app/.env`
```env
AWS_REGION=us-east-1
ENVIRONMENT=dev
PROJECT_NAME=strands-agent-chatbot
```
> เปลี่ยน `us-east-1` เป็น region ที่ใช้ (ต้องมี Bedrock access ใน region นั้น)

### `chatbot-app/frontend/.env.local`
```env
NEXT_PUBLIC_AGENTCORE_URL=http://localhost:8080
NEXT_PUBLIC_AGENTCORE_LOCAL=true
NEXT_PUBLIC_COGNITO_USER_POOL_ID=
NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID=
```

---

## Step 4: Install Dependencies

### Backend (Python)
```bash
cd chatbot-app/agentcore

# สร้าง virtual environment ด้วย Python 3.13
python3.13 -m venv venv        # Linux/macOS
py -3.13 -m venv venv          # Windows

# Activate
source venv/bin/activate       # Linux/macOS
.\venv\Scripts\activate        # Windows

# Install
pip install --upgrade pip
pip install -r requirements.txt
pip install nova-act --no-deps

# Install local tool packages (replaces Gateway Lambda tools)
pip install duckduckgo-search beautifulsoup4 Wikipedia-API arxiv yfinance
```

### Frontend (Node.js)
```bash
cd chatbot-app/frontend
npm install
```

---

## Step 5: รัน

### Terminal 1 — Backend
```bash
cd chatbot-app/agentcore
source venv/bin/activate       # Linux/macOS
# .\venv\Scripts\activate      # Windows

cd src
python main.py
```
→ http://localhost:8080 (API Docs: http://localhost:8080/docs)

### Terminal 2 — Frontend
```bash
cd chatbot-app/frontend
npm run dev
```
→ http://localhost:3000

---

## Step 6: ใช้งาน

1. เปิด http://localhost:3000
2. จะเข้าหน้า chat ได้เลย (ไม่มี login, ใช้ anonymous mode)
3. เลือก model ได้จาก model picker (Nova Pro / Lite / Micro)
4. พิมพ์ข้อความแล้ว Enter

---

## ความสามารถของระบบเต็ม vs ตอนนี้

ตารางด้านล่างแสดง **ทุกอย่างที่ระบบเต็มทำได้** เทียบกับสถานะ local ปัจจุบัน:

| # | Feature (ระบบเต็ม) | สถานะ Local | หมายเหตุ |
|---|-------------------|------------|----------|
| 1 | **Chat กับ AI** (Claude Sonnet/Haiku/Opus) | ✅ ทำได้ (ใช้ Nova Pro แทน) | เปลี่ยน model ได้ |
| 2 | **Multi-turn conversation** | ✅ ทำได้ | |
| 3 | **Model picker** (เลือก 15+ models) | ✅ ทำได้ (Nova Pro/Lite/Micro) | เพิ่ม model อื่นได้ใน available-models |
| 4 | **Web Search** (DuckDuckGo) | ✅ ทำได้ (local tool) | |
| 5 | **URL Content Fetching** | ✅ ทำได้ (local tool) | |
| 6 | **Wikipedia Search & Articles** | ✅ ทำได้ (local tool) | |
| 7 | **ArXiv Paper Search** | ✅ ทำได้ (local tool) | |
| 8 | **Finance** (stock quote, history, analysis) | ✅ ทำได้ (local tool) | |
| 9 | **Weather** (current + forecast) | ✅ ทำได้ (local tool) | |
| 10 | **Visualization** (charts: bar, line, pie) | ✅ ทำได้ | อยู่ใน local_tools เดิม |
| 11 | **Excalidraw Diagrams** | ✅ ทำได้ | อยู่ใน local_tools เดิม |
| 12 | **Session history** (จำบทสนทนา) | ✅ ทำได้ (local file) | ไม่ข้ามเครื่อง |
| 13 | **User Login / Signup** | ❌ ไม่ได้ | ต้อง Cognito |
| 14 | **Per-user data isolation** | ❌ ไม่ได้ | ทุกคนเป็น anonymous เดียวกัน |
| 15 | **Long-term Memory** (summarization, user facts) | ❌ ไม่ได้ | ต้อง AgentCore Memory |
| 16 | **Google Search** (premium) | ❌ ไม่ได้ | ต้อง API Key |
| 17 | **Google Maps** | ❌ ไม่ได้ | ต้อง API Key |
| 18 | **Tavily Search** (AI-optimized) | ❌ ไม่ได้ | ต้อง API Key |
| 19 | **Code Interpreter** (run Python/JS safely) | ❌ ไม่ได้ | ต้อง AgentCore Code Interpreter |
| 20 | **Browser Automation** (Nova Act) | ❌ ไม่ได้ | ต้อง AgentCore Browser |
| 21 | **Research Agent** (deep research via A2A) | ❌ ไม่ได้ | ต้อง AgentCore Runtime container |
| 22 | **Code Agent** (Claude Code via A2A) | ❌ ไม่ได้ | ต้อง AgentCore Runtime container |
| 23 | **Voice Mode** (real-time speech) | ❌ ไม่ได้ | ต้อง Nova Sonic 2 |
| 24 | **Gmail** (read/search/delete) | ❌ ไม่ได้ | ต้อง 3LO OAuth + MCP Runtime |
| 25 | **Google Calendar** | ❌ ไม่ได้ | ต้อง 3LO OAuth + MCP Runtime |
| 26 | **GitHub** (repos, issues, PRs) | ❌ ไม่ได้ | ต้อง 3LO OAuth + MCP Runtime |
| 27 | **Notion** (pages, databases) | ❌ ไม่ได้ | ต้อง 3LO OAuth + MCP Runtime |
| 28 | **Word Document generation** | ❌ ไม่ได้ | ต้อง Code Interpreter |
| 29 | **Excel Spreadsheet generation** | ❌ ไม่ได้ | ต้อง Code Interpreter |
| 30 | **PowerPoint generation** | ❌ ไม่ได้ | ต้อง Code Interpreter |
| 31 | **Prompt Caching** (ลดค่า token) | ❌ ไม่ได้ | เฉพาะ Claude เท่านั้น |
| 32 | **Observability** (tracing, metrics) | ❌ ไม่ได้ | ต้อง AgentCore Observability |
| 33 | **Production hosting** (scalable, CDN) | ❌ ไม่ได้ | ต้อง ECS + CloudFront |

**สรุป: ✅ 12/33 features ใช้งานได้ตอนนี้** (ในนั้น 7 ตัวเป็น local tool ที่เพิ่มเข้ามาแทน Gateway)

---

## สิ่งที่ใช้งานได้ / ไม่ได้ (รายละเอียด)

### ✅ ใช้งานได้ (ใช้ของทดแทน local)

| Feature | ตอนนี้ใช้อะไร (Local) | ถ้า deploy จริงจะเปลี่ยนเป็น | ต้อง revert อะไร |
|---------|---------------------|---------------------------|-----------------|
| **LLM Model** | Amazon Nova Pro (Bedrock API ตรง) | Claude Sonnet/Haiku (Bedrock API ตรง) | เปลี่ยน `DEFAULT_MODEL_ID` กลับเป็น Claude + `max_tokens=32000` |
| **Gateway Tools** | Local Python functions (in-process) | AgentCore Gateway → Lambda | ลบ local tool imports จาก `local_tools/__init__.py`, deploy Gateway + Lambda |
| **Session Storage** | Local file (`agentcore/sessions/`) | DynamoDB | ลบ `.env.local` → `NEXT_PUBLIC_AGENTCORE_LOCAL` จะเป็น false → ใช้ DynamoDB อัตโนมัติ |
| **Conversation Memory** | Local file (short-term only, ไม่มี summarize) | AgentCore Memory (short-term + long-term + summarization) | Set `MEMORY_ID` env var → ระบบจะใช้ AgentCore Memory |
| **User Identity** | Anonymous mode (ทุกคนเป็น user เดียวกัน) | Cognito (login/signup/JWT per-user) | ใส่ `NEXT_PUBLIC_COGNITO_USER_POOL_ID` + `CLIENT_ID` ใน `.env.local` |
| **Model Config** | Local JSON file | DynamoDB (per-user preferences) | เหมือน session — ลบ `NEXT_PUBLIC_AGENTCORE_LOCAL=true` |
| **Backend Runtime** | Python process ตรงๆ (uvicorn) | AgentCore Runtime (managed container) | Deploy ด้วย Terraform `module.runtime_orchestrator` |
| **Frontend Hosting** | `npm run dev` (localhost:3000) | ECS Fargate + CloudFront | Deploy ด้วย Terraform `module.chat` |

### ❌ ไม่ทำงานเลย (ไม่มี fallback, ต้อง deploy)

| Feature | ต้องมี AWS Service | Terraform Module | หมายเหตุ |
|---------|-------------------|------------------|----------|
| **Code Interpreter** | AgentCore Code Interpreter | ต้อง enable AgentCore ใน account | Sandbox ที่รัน Python/JS อย่างปลอดภัย |
| **Browser Automation** | AgentCore Browser + Nova Act Workflow | ต้อง enable AgentCore + สร้าง workflow | Headless browser + visual AI model |
| **Research Agent (A2A)** | AgentCore Runtime container | `module.runtime` (type=a2a_agent) | Container แยกที่รัน research agent |
| **Code Agent (A2A)** | AgentCore Runtime + S3 workspace | `module.runtime` (type=a2a_agent) | Claude Code SDK ทำ coding tasks |
| **Voice Mode** | Nova Sonic 2 (bidirectional WebSocket) | ต้อง Runtime deployed | Real-time voice ↔ text |
| **Long-term Memory Summarization** | AgentCore Memory | `module.memory` | Auto-summarize บทสนทนายาว |
| **3LO OAuth** (Gmail, Calendar, GitHub, Notion) | AgentCore MCP Runtime + OAuth credentials | `module.runtime` (mcp) | ต้อง register OAuth app กับ provider |
| **Prompt Caching** | Claude model (feature เฉพาะ Anthropic) | — | Nova ไม่รองรับ, เปลี่ยนกลับ Claude ถึงจะใช้ได้ |

### ✅ เพิ่มเข้ามาแล้ว — Local tools ทดแทน Gateway (ไม่ต้อง infra)

Tools ด้านล่างถูก copy logic จาก Lambda มาเป็น local tool แล้ว ใช้งานได้ทันที:

| Feature | Local tool file | Package ที่ลงแล้ว | ถ้า deploy จริง → เปลี่ยนเป็น | Deploy command |
|---------|----------------|------------------|-------------------------------|----------------|
| **Web Search (DuckDuckGo)** | `local_tools/web_search.py` | `duckduckgo-search` | Lambda `web-search` via AgentCore Gateway MCP | `terraform apply -target=module.gateway` |
| **URL Fetcher** | `local_tools/web_search.py` | `beautifulsoup4` | Lambda `web-search` via AgentCore Gateway MCP | เหมือนข้างบน |
| **Wikipedia Search** | `local_tools/wikipedia_search.py` | `Wikipedia-API` | Lambda `wikipedia` via AgentCore Gateway MCP | `terraform apply -target=module.gateway` |
| **Wikipedia Article** | `local_tools/wikipedia_search.py` | `Wikipedia-API` | Lambda `wikipedia` via AgentCore Gateway MCP | เหมือนข้างบน |
| **ArXiv Paper Search** | `local_tools/arxiv_search.py` | `arxiv` | Lambda `arxiv` via AgentCore Gateway MCP | `terraform apply -target=module.gateway` |
| **Finance (Stock Quote/History/Analysis)** | `local_tools/finance.py` | `yfinance` | Lambda `finance` via AgentCore Gateway MCP | `terraform apply -target=module.gateway` |
| **Weather (Current + Forecast)** | `local_tools/weather.py` | ไม่ต้อง (urllib built-in) | Lambda `weather` via AgentCore Gateway MCP | `terraform apply -target=module.gateway` |

> **หมายเหตุ:** เมื่อ deploy จริง ต้องลบ imports ของ tools เหล่านี้ออกจาก `local_tools/__init__.py`  
> เพราะ tools จะมาจาก AgentCore Gateway (MCP protocol → Lambda) แทนการเรียก function ตรงๆ  
> Lambda source code อยู่ที่ `agentcore/gateway-tools/lambda-functions/`

### ⚠️ เพิ่มได้เองเพิ่มเติม (ยังไม่ได้ทำ, ต้องมี API Key)

| Feature | Package ที่ต้องลง | Source code อ้างอิง | API Key? |
|---------|------------------|-------------------|----------|
| Google Search | `google-api-python-client` | `lambda-functions/google-search/` | ต้อง Google API Key |
| Google Maps | `googlemaps` | `lambda-functions/google-maps/` | ต้อง Google Maps Key |
| Tavily Search | `tavily-python` | `lambda-functions/tavily/` | ต้อง Tavily Key |

---

## ค่าใช้จ่าย

- **Bedrock (Nova Pro):** ~$0.0008/1K input tokens, ~$0.0032/1K output tokens
- **ไม่มี resource อื่น:** ไม่มี EC2, Lambda, DynamoDB ถูกสร้าง
- **ค่าใช้จ่ายเกิดเฉพาะตอนส่งข้อความ chat**

---

## Troubleshooting

| ปัญหา | วิธีแก้ |
|--------|---------|
| `ModuleNotFoundError: No module named 'nova_act'` | `pip install nova-act --no-deps` |
| `max_tokens exceeds model limit` | แก้ `max_tokens` เป็น 5000 (ดู Step 2.2) |
| `ResourceNotFoundException` (DynamoDB) | เช็คว่า `chatbot-app/frontend/.env.local` มี `NEXT_PUBLIC_AGENTCORE_LOCAL=true` |
| `ParameterNotFound` (SSM) | ปกติ — ระบบ fallback ใช้ local storage |
| `Amplify has not been configured` | ปกติ — ไม่มี Cognito ระบบใช้ anonymous mode |
| `node is not recognized` | เพิ่ม Node.js ลง PATH หรือ restart terminal หลังลง Node.js |
| `Python version < 3.13` | package `aws-sdk-bedrock-runtime` ต้อง Python 3.12+ |
| Backend ไม่ reload หลังแก้ไฟล์ | ปกติ auto-reload แต่ถ้าไม่ — กด Ctrl+C แล้วรันใหม่ |

---

## โครงสร้างที่เกี่ยวข้อง

```
chatbot-app/
├── .env                    ← สร้างเอง (AWS config)
├── agentcore/
│   ├── venv/               ← สร้างจาก Step 4
│   ├── src/
│   │   ├── main.py         ← Entry point (FastAPI, port 8080)
│   │   ├── agents/         ← Agent logic + model factory
│   │   ├── agent/config/   ← Constants, prompt builder
│   │   ├── local_tools/    ← Web search, Wikipedia, Finance, Weather + Visualization, Excalidraw
│   │   └── routers/        ← API routes
│   ├── skills/             ← Skill definitions (SKILL.md)
│   ├── sessions/           ← Local session storage (auto-created)
│   └── requirements.txt
└── frontend/
    ├── .env.local          ← สร้างเอง (local mode flags)
    ├── src/
    │   ├── app/api/        ← BFF routes (model, stream, session)
    │   ├── components/     ← Chat UI components
    │   ├── hooks/          ← useChat, useChatAPI
    │   └── config/         ← Session config
    ├── package.json
    └── node_modules/       ← สร้างจาก npm install
```

---

## ถ้าจะ Deploy จริง — สิ่งที่ต้อง Revert กลับ

รายการด้านล่างคือทุกจุดที่แก้สำหรับ local dev ถ้าจะ deploy ขึ้น production ต้องเปลี่ยนกลับ:

### 1. Model — เปลี่ยนกลับเป็น Claude

| ไฟล์ | เปลี่ยนจาก (local) | เปลี่ยนเป็น (production) |
|------|--------------------|-----------------------|
| `agentcore/src/agent/config/constants.py` | `us.amazon.nova-pro-v1:0` | `us.anthropic.claude-haiku-4-5-20251001-v1:0` |
| `agentcore/src/agents/base.py` | `us.amazon.nova-pro-v1:0` | `us.anthropic.claude-haiku-4-5-20251001-v1:0` |
| `agentcore/src/agents/workflow_agent.py` | `us.amazon.nova-pro-v1:0` | `us.anthropic.claude-sonnet-4-6` |
| `agentcore/src/workflows/composer_workflow.py` | `us.amazon.nova-pro-v1:0` | `us.anthropic.claude-sonnet-4-6` |

### 2. max_tokens — เปลี่ยนกลับเป็น 32000

| ไฟล์ | เปลี่ยนจาก (local) | เปลี่ยนเป็น (production) |
|------|--------------------|-----------------------|
| `agentcore/src/agents/model_factory.py` | `max_tokens: int = 5000` | `max_tokens: int = 32000` |
| `agentcore/src/agents/chat_agent.py` | `max_tokens=5000` | `max_tokens=32000` |

### 3. Frontend defaults — เปลี่ยนกลับเป็น Claude

| ไฟล์ | เปลี่ยนจาก (local) | เปลี่ยนเป็น (production) |
|------|--------------------|-----------------------|
| `frontend/src/hooks/useChat.ts` | `us.amazon.nova-pro-v1:0` | `us.anthropic.claude-sonnet-4-6` |
| `frontend/src/app/api/stream/chat/route.ts` | `us.amazon.nova-pro-v1:0` | `us.anthropic.claude-sonnet-4-6` |
| `frontend/src/app/api/model/config/route.ts` | `us.amazon.nova-pro-v1:0` | `us.anthropic.claude-sonnet-4-6` |
| `frontend/src/app/api/model/available-models/route.ts` | Nova models ด้านบน | ลบ Nova models ออก (optional, เก็บไว้ก็ได้) |

### 4. Local Tools — ลบ local replacements

เมื่อ deploy Gateway + Lambda แล้ว ต้อง **ลบ** local tool imports ออก:

**ไฟล์:** `agentcore/src/local_tools/__init__.py`
```python
# ลบบรรทัดเหล่านี้ออก (tools จะมาจาก Gateway MCP แทน):
from .web_search import ddg_web_search, fetch_url_content
from .wikipedia_search import wikipedia_search, wikipedia_get_article
from .arxiv_search import arxiv_search, arxiv_get_paper
from .finance import stock_quote, stock_history, stock_analysis
from .weather import get_today_weather, get_weather_forecast
```

หลัง deploy แล้ว tools เหล่านี้จะมาจาก **AgentCore Gateway → Lambda** แทน โดย:
- Gateway ใช้ MCP protocol เรียก Lambda
- Lambda code อยู่ที่ `agentcore/gateway-tools/lambda-functions/`
- Deploy ด้วย: `./infra/scripts/deploy.sh apply -target=module.gateway`

### 5. Environment files — เปลี่ยน/ลบ

| ไฟล์ | ทำอะไร |
|------|--------|
| `chatbot-app/.env` | เปลี่ยนค่าให้ตรงกับ Terraform output (Cognito IDs, Memory ID ฯลฯ) |
| `chatbot-app/frontend/.env.local` | **ลบ** `NEXT_PUBLIC_AGENTCORE_LOCAL=true` (หรือลบไฟล์ทิ้ง) ใส่ Cognito IDs แทน |

### 6. Warmup skip — ลบออก

**ไฟล์:** `frontend/src/config/session.ts`
```python
# ลบบรรทัดนี้ออก:
if (process.env.NEXT_PUBLIC_AGENTCORE_LOCAL === 'true') {
  return
}
```

### 7. Deploy infrastructure

```bash
# ตั้งค่า
cp infra/environments/dev/terraform.tfvars.example infra/environments/dev/terraform.tfvars
# แก้ไข terraform.tfvars

# Deploy ทีละส่วนหรือทั้งหมด:
./infra/scripts/deploy.sh apply                          # ทั้งหมด
./infra/scripts/deploy.sh apply -target=module.auth      # Cognito เท่านั้น
./infra/scripts/deploy.sh apply -target=module.gateway   # Gateway + Lambda tools
./infra/scripts/deploy.sh apply -target=module.memory    # AgentCore Memory
./infra/scripts/deploy.sh apply -target=module.chat      # Frontend (ECS + CloudFront)
./infra/scripts/deploy.sh apply -target=module.runtime_orchestrator  # Agent Runtime
```

### สรุป mapping: Local → Production

| ของ Local (ชั่วคราว) | ของ Production (จริง) | Deploy ยังไง |
|---------------------|---------------------|-------------|
| Nova Pro | Claude Sonnet/Haiku | แก้ `DEFAULT_MODEL_ID` + enable Claude ใน Bedrock Console |
| `local_tools/web_search.py` | Lambda `web-search` via Gateway MCP | `terraform apply -target=module.gateway` |
| `local_tools/wikipedia_search.py` | Lambda `wikipedia` via Gateway MCP | `terraform apply -target=module.gateway` |
| `local_tools/arxiv_search.py` | Lambda `arxiv` via Gateway MCP | `terraform apply -target=module.gateway` |
| `local_tools/finance.py` | Lambda `finance` via Gateway MCP | `terraform apply -target=module.gateway` |
| `local_tools/weather.py` | Lambda `weather` via Gateway MCP | `terraform apply -target=module.gateway` |
| Local file sessions | DynamoDB | `terraform apply -target=module.data` |
| Anonymous mode | Cognito User Pool | `terraform apply -target=module.auth` |
| Local file memory | AgentCore Memory | `terraform apply -target=module.memory` |
| `python main.py` (uvicorn) | AgentCore Runtime (container) | `terraform apply -target=module.runtime_orchestrator` |
| `npm run dev` (localhost) | ECS Fargate + CloudFront | `terraform apply -target=module.chat` |
