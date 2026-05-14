# paper2diagram-agent 项目说明

## 一、项目做什么

**paper2diagram-agent** 是一个本地可运行的流水线：从论文 **PDF** 中抽取 **Method / Architecture** 相关内容，用 **Gemini** 提炼主干结构与评审式要点，再生成多张**学术风格配图**的英文 Prompt，通过网关上的 **nano_banana**（兼容 OpenAI `chat/completions`）出图，并将图片保存到 `outputs/`。

典型用途：快速得到「方法结构图 + 创新点示意 + 实验对比风格图」等，辅助汇报或笔记（**不能替代**对论文的完整人工阅读）。

---

## 二、技术结构（简版）

| 模块 | 作用 |
|------|------|
| `app/main.py` / `app/openclaw_main.py` | 命令行入口 |
| `app/orchestrator/pipeline.py` | 串联全流程 |
| `app/skills/pdf_reader.py` | PDF 文本抽取 |
| `app/skills/section_extractor.py` | 定位方法/架构片段（含兜底） |
| `app/skills/logic_distiller.py` | 调用 Gemini 生成结构化 JSON |
| `app/skills/prompt_translator.py` | 生成多图英文 Prompt |
| `app/skills/banana_renderer.py` | 调用出图接口 |
| `app/clients/gemini_client.py` | Gemini REST（支持官方与兼容网关） |
| `app/clients/banana_client.py` | 图像侧：`POST /v1/chat/completions` + 解析 URL |
| `skills/paper2diagram/SKILL.md` | 发布到 ClawHub 的技能说明（不含密钥） |

环境变量见 `.env.example`。

---

## 三、实现过程中遇到的问题与处理

### 1. 只改 `.env.example` 不生效

**现象**：配置了网关地址，运行仍走默认 Google 地址。  
**原因**：`python-dotenv` 默认只加载项目根目录的 `.env`，不读取 `.env.example`。  
**处理**：在 `.env` 中填写真实配置；`.env.example` 仅作模板。

### 2. `GEMINI_BASE_URL` 只填域名根路径，返回 HTML「New API」首页

**现象**：解析 JSON 报错，响应体是 `<!doctype html>`。  
**原因**：请求打到了站点首页，而不是 Gemini REST。正确路径形如：`{host}/v1beta/models/{model}:generateContent`。  
**处理**：将 `GEMINI_BASE_URL` 设为带 **`/v1beta`** 的前缀（以网关文档为准），例如 `https://example.com/v1beta`。

### 3. 鉴权方式不一致（`?key=` vs `Bearer`）

**现象**：401 或空响应。  
**原因**：官方 Google 用 `?key=`，部分兼容网关用 `Authorization: Bearer`。  
**处理**：在 `gemini_client.py` 中按 `base_url` 是否包含 `generativelanguage.googleapis.com` 分支；并增加 `GEMINI_USE_QUERY_KEY` 供网关统一走 query key。

### 4. Gemini 请求超时

**现象**：`The read operation timed out`。  
**原因**：代理慢、长文本、默认超时过短。  
**处理**：使用 `httpx.Timeout` 分离 connect / read；提高 `GEMINI_TIMEOUT_SECONDS`；`logic_distiller` 对输入截断以降低延迟。

### 5. Banana 出图路径与模型名错误

**现象**：`/v1/images/generations` 报「无可用通道」或模型 `nano-banana` 不存在。  
**原因**：当前网关上该模型挂在 **`/v1/chat/completions`**，且模型 id 为 **`nano_banana_pro-1K`** 等形式，而非传统 OpenAI Images API。  
**处理**：`banana_client.py` 改为调用 `chat/completions`，从 `choices[0].message.content` 中用正则提取首个 `http(s)` 图片链接；`.env` 中 `BANANA_MODEL` 与控制台一致。

### 6. 403 / 503 / 余额不足

**现象**：部分图成功、部分失败；或全部 403。  
**原因**：网关账户额度、并发、上游图像服务不可用。  
**处理**：对 502/503/504 做有限重试；明确错误信息；用户侧充值或换时段；可选 `ENABLE_BANANA=false` 仅跑分析与 Prompt。

### 7. 图片链接短期有效、浏览器打开 404

**现象**：返回的 OSS URL 一段时间后失效。  
**原因**：临时签名或 CDN 策略。  
**处理**：在 `pipeline` 中成功出图后立即下载到 `outputs/`，以本地文件为准。

### 8. ClawHub 发布 skill

**现象**：`clawhub skill publish` 不存在；`sync` 扫描到重复 slug 显示已同步。  
**原因**：CLI 版本以 `clawhub sync` 为主；默认 workdir 可能扫到 `~/.openclaw/workspace/skills` 与仓库两份。  
**处理**：使用 `clawhub --workdir . sync --root ./skills/paper2diagram` 并带 `--bump` / `--changelog`；`SKILL.md` 用中文说明 + `metadata` 声明所需 env，降低安全扫描误报。

### 9. 发布不包含 `.env`

**说明**：ClawHub 仅托管技能包与说明，**不会**带上你的密钥。使用者需在本地或 OpenClaw `skills.entries` 中自行配置 `GEMINI_*`、`BANANA_*` 等。

---

## 四、如何运行（备忘）

```bash
cd /path/to/paper2diagram-agent
source .venv/bin/activate
cp .env.example .env   # 首次：编辑 .env
python -m app.openclaw_main local "/绝对路径/论文.pdf" 30
```

出图结果：终端 JSON 中的 `render_results`，以及目录 `outputs/` 下按论文名命名的 `*.jpg`。

---

## 五、后续可改进方向（可选）

- 在线 PDF URL 下载后再解析  
- 结构化输出强制 JSON Schema 校验（减少 Gemini 返回非 JSON）  
- Banana 失败时仅重试失败子图  
- 提供 Docker 一键部署，便于他人复现  

---

*文档随项目演进可继续补充版本号与变更记录。*
