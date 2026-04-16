# smart-filer

`smart-filer` 是一个面向 Windows 本地环境的 CLI 助手。

当前版本刻意保持范围很小：输入一个软件名称，输出结构化的“建议安装位置”结果。
本版本只做“建议”，不做任何自动执行（不移动文件、不拉起安装程序）。

## 当前已实现（Scope）

- 输入一个软件名称（例如：`OBS Studio`、`Altium Designer`、`7-Zip`）。
- 从本地规则文档 `文档结构.rule.md` 解析安装路径相关规则。
- 可选：调用 SiliconFlow（OpenAI 兼容 API）做软件类别推断。
- 应用硬规则：软件建议优先落在 `D:` 盘体系，且不建议安装到 `S:` 盘。
- 输出结构化 JSON：包含建议（suggestion）+ 说明（explanation）+ 回退信息。
- CLI 命令：`suggest-install-path`。

## 当前未实现（明确不做）

- 文件路由、文件移动/重命名执行。
- 安装程序执行与回滚。
- 本机已安装软件清单扫描。
- 按“功能”查找软件（能力标签检索）。
- `watch` 监听模式/后台服务。
- SQLite 持久化索引/历史。

## 规则来源与优先级

1. 本地规则文档：`文档结构.rule.md`（解析为 `ParsedInstallRules`）。
2. 领域层硬规则（hard constraints）。
3. LLM 输出仅作参考（advisory）。

当本地硬规则与 LLM 输出冲突时，永远以本地硬规则为准。

## 快速开始（如何使用）

前提：
- Windows + Python 3.12
- 依赖管理使用 `uv`
- 规则文档默认使用仓库根目录下的 `文档结构.rule.md`

### 1) 安装依赖（推荐按文档设置 venv/cache 落点）

依赖安装与环境落点规范见：`docs/dependency-installation.md`。

### 2) 直接运行命令（LLM 关闭，走保守回退建议）

```powershell
$env:SMART_FILER_RULES_DOCUMENT_PATH = "文档结构.rule.md"
$env:SMART_FILER_LLM_ENABLED = "false"
uv run smart-filer suggest-install-path "OBS Studio"
```

### 3) 启用 LLM（SiliconFlow）

```powershell
$env:SMART_FILER_RULES_DOCUMENT_PATH = "文档结构.rule.md"
$env:SMART_FILER_LLM_ENABLED = "true"
$env:SMART_FILER_SILICONFLOW_API_KEY = "<your-key>"
$env:SMART_FILER_SILICONFLOW_MODEL_ID = "<model-id>"
# 可选（有默认值）
$env:SMART_FILER_SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
$env:SMART_FILER_REQUEST_TIMEOUT_SECONDS = "30"
uv run smart-filer suggest-install-path "Altium Designer"
```

模型 ID 请以 SiliconFlow 控制台可用模型为准：`https://cloud.siliconflow.cn/me/models`

## 输出格式（示例）

```powershell
smart-filer suggest-install-path "OBS Studio"
```

输出为结构化 JSON，顶层包含 `suggestion` 与 `explanation`：

```json
{
  "suggestion": {
    "software_name": "OBS Studio",
    "software_category": "media_design",
    "suggested_install_path": "D:\\50_Media_Design",
    "reason": "...",
    "confidence": 0.91,
    "needs_confirmation": true,
    "fallback_status": "not_used",
    "fallback_used": false,
    "rule_basis": [
      {
        "source": "llm",
        "priority": 200,
        "summary": "..."
      }
    ]
  },
  "explanation": {
    "why_this_path": "...",
    "rule_basis": ["..."],
    "fallback_note": "..."
  }
}
```

## 配置（环境变量）

环境变量统一前缀：`SMART_FILER_`。

- `RULES_DOCUMENT_PATH`：规则文档路径（默认：`文档结构.rule.md`）。
- `LLM_ENABLED`：是否启用 LLM（`true`/`false`）。
- `SILICONFLOW_API_KEY`：SiliconFlow API Key（仅 LLM 启用时必填）。
- `SILICONFLOW_MODEL_ID`：模型 ID（仅 LLM 启用时必填）。
- `SILICONFLOW_BASE_URL`：默认 `https://api.siliconflow.cn/v1`。
- `REQUEST_TIMEOUT_SECONDS`：请求超时（秒）。
- `FALLBACK_REQUIRES_CONFIRMATION`：是否要求人工确认（当前版本默认/实际都为 true）。

## LLM 回退策略（何时会 fallback）

以下任一情况会触发回退，输出保守建议并强制 `needs_confirmation = true`：

- SiliconFlow 请求失败/超时。
- 结构化响应无效（非 JSON 或 schema 校验失败）。
- 置信度低于阈值。
- LLM 给出的路径不在 `D:` 盘体系内，或落在 `S:` 盘。
- 类别与规则文档解析得到的映射冲突。

## 开发与测试

```powershell
uv run pytest -s tests/test_step17_integration_cli_pipeline.py
uv run pytest -s tests
```

## 验收清单（Step 18）

- [x] 明确当前只支持“软件安装位置建议”。
- [x] 说明 CLI 用法与输入输出结构。
- [x] 说明规则来源与优先级。
- [x] 说明依赖安装路径规则与参考文档。
- [x] 说明 SiliconFlow 配置与模型来源。
- [x] 说明回退策略与保守建议行为。
- [x] 明确未实现能力边界。
