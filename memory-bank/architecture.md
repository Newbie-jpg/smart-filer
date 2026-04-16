# smart-filer 架构说明（当前实现）

## 1. 当前架构状态（截至 2026-04-16）

- 本仓库已完成实施计划步骤 1-16。
- 当前处于“CLI 入口已接入，等待步骤17集成测试”阶段：
  - 已完成目录分层、依赖声明、配置加载、日志初始化。
  - 已完成领域模型定义（软件类别、规则元数据、安装建议结果）。
  - 已完成 LLM 请求/响应结构化模型定义（含字段约束与别名映射）。
  - 已完成规则文档加载器（仅负责读取文本，和业务解析解耦）。
  - 已完成规则文档解析器（提取 D 盘优先、S 盘约束、类别路径映射）。
  - 已完成安装路径硬规则服务（映射优先、非法路径纠正）。
  - 已完成 SiliconFlow provider adapter（OpenAI 兼容方式、超时与错误包装、原始响应记录）。
  - 已完成独立提示词构建器（与 provider adapter 解耦）。
  - 已完成 LLM 响应解析与回退服务（统一产出 `InstallSuggestion`）。
  - 已完成软件安装建议应用层用例编排（规则加载、请求组装、LLM 调用、回退守卫、结构化输出）。
  - 已完成结果说明与规则依据整理服务（稳定可读说明、规则依据排序、回退状态说明）。
  - 已完成 CLI 根入口（Typer app、顶层异常处理、统一输出通道）。
  - 已完成 `suggest-install-path` 命令（调用用例并输出结构化 JSON）。
- 当前未完成：步骤17集成测试、步骤18文档验收清单。

## 2. 分层与依赖方向

- 依赖方向遵循：
  - `cli -> application -> domain`
  - `application -> infrastructure`
  - `infrastructure -> domain`
- 当前关键实现：
  - `smart_filer/main.py`：CLI 进程入口（退出码透传）
  - `smart_filer/cli/app.py`：Typer 根应用与顶层异常处理
  - `smart_filer/cli/output.py`：统一 JSON/错误输出
  - `smart_filer/cli/commands/suggest_install_path.py`：安装路径建议命令
  - `smart_filer/config.py`：跨层共享配置入口
  - `smart_filer/infrastructure/logging_setup.py`：统一日志初始化入口
  - `smart_filer/domain/models/*`：领域模型
  - `smart_filer/domain/models/llm_models.py`：LLM 请求/响应结构化模型
  - `smart_filer/infrastructure/rules/document_loader.py`：规则文档读取适配器
  - `smart_filer/infrastructure/rules/document_parser.py`：规则文档解析器
  - `smart_filer/domain/services/install_path_hard_rules.py`：安装路径硬规则服务
  - `smart_filer/infrastructure/providers/prompt_builder.py`：提示词构建器
  - `smart_filer/infrastructure/providers/siliconflow_adapter.py`：SiliconFlow 适配器
  - `smart_filer/application/services/llm_response_service.py`：LLM 响应解析与回退服务
  - `smart_filer/application/use_cases/install_path_suggestion.py`：软件安装位置建议用例编排
  - `smart_filer/application/services/suggestion_explainer.py`：结果说明与规则依据整理

## 3. 领域模型设计（步骤5）

### 3.1 软件类别枚举

- 模块：`smart_filer/domain/models/software_category.py`
- 对象：`SoftwareCategory`
- 受控枚举值：
  - `development_environment`
  - `engineering`
  - `productivity`
  - `media_design`
  - `system_utilities`
  - `games_entertain`
  - `unknown`

### 3.2 规则元数据对象

- 模块：`smart_filer/domain/models/rule_metadata.py`
- 对象：
  - `RuleSource`（`document`/`hard_rule`/`llm`/`fallback`）
  - `RulePriority`（`IntEnum`，定义规则优先级）
  - `FallbackStatus`（回退状态）
  - `RuleBasis`（结构化规则依据项）

### 3.3 安装建议结果对象

- 模块：`smart_filer/domain/models/install_suggestion.py`
- 对象：`InstallSuggestion`
- 关键约束：
  - `software_name`、`suggested_install_path`、`reason` 非空
  - `confidence` 范围 `[0.0, 1.0]`
  - `rule_basis` 至少一条
  - `fallback_used` 与 `fallback_status` 保持一致
  - 当前版本强制 `needs_confirmation = true`

### 3.4 LLM 请求与响应对象（步骤9）

- 模块：`smart_filer/domain/models/llm_models.py`
- 对象：
  - `LLMInstallPathRequest`
    - 字段：`software_name`、`rule_summary`、`aliases`、`context`
    - 约束：`software_name` 非空、`rule_summary` 至少一条且成员不为空字符串
  - `LLMInstallPathResponse`
    - 字段：`software_category`、`suggested_install_path`、`reason`、`confidence`
    - 对齐 LLM 输出别名：`category` -> `software_category`，`suggested_path` -> `suggested_install_path`
    - 约束：`suggested_install_path`、`reason` 非空；`confidence` 范围 `[0.0, 1.0]`

## 4. 规则文档加载器设计（步骤6）

- 模块：`smart_filer/infrastructure/rules/document_loader.py`
- 能力边界：
  - 只读取原始文档文本
  - 不做规则提取和业务解析
- 异常语义：
  - `RulesDocumentError: does not exist`
  - `RulesDocumentError: path is not a file`
  - `RulesDocumentError: invalid UTF-8`
  - `RulesDocumentError: is empty`

## 5. SiliconFlow 适配器与提示词构建（步骤10-11）

- 模块：`smart_filer/infrastructure/providers/siliconflow_adapter.py`
- 核心对象：
  - `SiliconFlowAdapter`：封装 OpenAI 兼容调用，隔离 provider 细节
  - `SiliconFlowAdapterResult`：返回结构化响应 + 原始响应文本 + 使用的 model ID
  - `SiliconFlowAdapterError` / `SiliconFlowTimeoutError` / `SiliconFlowResponseError`：项目内部错误语义
  - `InstallPathPromptBuilder`：独立负责 prompt 消息构建
- 关键行为：
  - 从配置注入 `base_url`、`model_id`、`timeout_seconds`
  - 请求时强制要求 JSON 结构化输出（`response_format = json_object`）
  - 对空响应、非 JSON、schema 校验失败进行明确错误包装
  - 记录原始响应文本，供后续审计与回放
  - prompt 组装逻辑已从 adapter 中抽离，便于独立测试与迭代

## 6. LLM 响应解析与回退服务（步骤12）

- 模块：`smart_filer/application/services/llm_response_service.py`
- 核心对象：
  - `build_install_suggestion_from_llm`：把 provider 输出转换为 `InstallSuggestion`
- 核心策略：
  - 若 LLM 响应合法且置信度达标，则输出正常建议并附加规则依据
  - 若出现以下任一情况，进入回退并强制人工确认：
    - provider 调用失败（如超时）
    - provider 结构化响应错误（如非法 JSON / schema 校验失败）
    - 低置信度结果
    - 非法路径（非 `D:` 或落在 `S:`）
    - 类别与规则映射冲突
- 回退结果约束：
  - 始终返回 `D:` 盘保守路径（`ParsedInstallRules.default_d_drive_path()`）
  - `fallback_used = true`
  - `fallback_status` 与失败原因严格对齐
  - `needs_confirmation = true`

## 7. 核心建议用例与说明整理（步骤13-14）

- 步骤13模块：`smart_filer/application/use_cases/install_path_suggestion.py`
- 核心对象：`SuggestInstallPathUseCase`
- 编排职责：
  - 校验输入软件名
  - 读取并解析规则文档
  - 生成稳定 `rule_summary` 并构建 `LLMInstallPathRequest`
  - 调用 SiliconFlow adapter（或注入的分类器）
  - 统一通过 `build_install_suggestion_from_llm` 执行硬规则与回退守卫
  - 输出 `InstallSuggestion`
- 关键容错：
  - LLM 未启用时回退
  - adapter 初始化失败回退
  - LLM 请求失败回退
  - 低置信度阈值可配置

- 步骤14模块：`smart_filer/application/services/suggestion_explainer.py`
- 核心对象：
  - `SuggestionExplanation`
  - `build_suggestion_explanation`
- 说明整理职责：
  - 生成“为何建议该路径”的稳定文本
  - 生成可读规则依据列表（含来源与优先级）
  - 输出回退状态与触发原因说明

## 8. CLI 入口与命令（步骤15-16）

- 步骤15模块：`smart_filer/cli/app.py`、`smart_filer/main.py`
- 核心对象：
  - `app`：CLI 根应用
  - `run_cli`：统一顶层异常处理并返回退出码
- 关键行为：
  - 根命令可直接启动并展示帮助信息
  - `--help` 可展示已注册命令
  - 顶层未知异常统一转为友好错误输出并以非零退出码返回

- 步骤16模块：`smart_filer/cli/commands/suggest_install_path.py`、`smart_filer/cli/output.py`
- 核心对象：
  - `suggest_install_path_command`：安装位置建议命令实现
  - `build_suggestion_payload`：统一输出结构
- 命令行为：
  - 输入软件名后调用 `SuggestInstallPathUseCase`
  - 输出结构化 JSON（建议 + 说明）
  - 空输入返回友好错误
  - 不可靠分类与 LLM 回退场景可稳定输出 fallback 结果

## 9. 测试覆盖概览

- `tests/test_step1_project_structure.py`：分层目录与包导入
- `tests/test_step2_project_metadata.py`：依赖声明与安装规则文档约束
- `tests/test_step3_config.py`：配置默认值、覆盖、关键字段校验
- `tests/test_step4_logging_setup.py`：日志初始化与幂等性
- `tests/test_step5_domain_models.py`：领域模型校验、枚举非法值、序列化反序列化
- `tests/test_step6_rules_document_loader.py`：规则文档读取、中文读取、异常场景
- `tests/test_step7_rule_document_parser.py`：规则提取（D盘优先/S盘约束/类别映射）与未知格式告警
- `tests/test_step8_install_path_hard_rules.py`：硬规则覆盖、S盘纠正、非D盘纠正与保留合法D盘路径
- `tests/test_step9_llm_models.py`：LLM 请求/响应模型字段校验、别名映射、缺失字段拒绝
- `tests/test_step10_siliconflow_adapter.py`：请求组装、配置透传、超时/空响应/非 JSON 错误包装
- `tests/test_step11_prompt_builder.py`：提示词输入完整性与顺序稳定性
- `tests/test_step12_llm_response_service.py`：合法解析与回退场景（非法 JSON/缺失字段/低置信度/S 盘路径/LLM 失败）
- `tests/test_step13_install_path_suggestion_use_case.py`：应用层主编排（五大类别 + 不可靠分类回退 + 人工确认）
- `tests/test_step14_suggestion_explainer.py`：说明文本稳定性、规则依据可读性、回退原因完整性
- `tests/test_step15_cli_root.py`：CLI 根入口帮助信息与顶层异常处理
- `tests/test_step16_cli_suggest_install_path_command.py`：建议命令正常输入、空输入、无法分类与 LLM 回退场景

最新验证结果：步骤1-16测试总计 `64 passed`。

## 10. 文件职责（当前实现）

- `smart_filer/main.py`：CLI 进程入口
- `smart_filer/cli/app.py`：Typer 根应用与顶层异常处理
- `smart_filer/cli/output.py`：统一输出工具
- `smart_filer/cli/commands/suggest_install_path.py`：建议命令
- `smart_filer/config.py`：全局配置定义与读取
- `smart_filer/infrastructure/logging_setup.py`：日志初始化
- `smart_filer/domain/models/software_category.py`：软件类别枚举
- `smart_filer/domain/models/rule_metadata.py`：规则来源/优先级/回退状态与规则依据对象
- `smart_filer/domain/models/install_suggestion.py`：安装建议结果模型
- `smart_filer/domain/models/llm_models.py`：LLM 请求与响应结构化模型
- `smart_filer/domain/models/parsed_rules.py`：规则文档解析后的中间表示
- `smart_filer/infrastructure/rules/document_loader.py`：规则文档原文加载
- `smart_filer/infrastructure/rules/document_parser.py`：规则文档解析器
- `smart_filer/domain/services/install_path_hard_rules.py`：安装路径硬规则服务
- `smart_filer/infrastructure/providers/prompt_builder.py`：提示词构建
- `smart_filer/infrastructure/providers/siliconflow_adapter.py`：SiliconFlow 调用适配与错误包装
- `smart_filer/application/services/llm_response_service.py`：LLM 响应解析与回退落地
- `smart_filer/application/use_cases/install_path_suggestion.py`：软件安装位置建议应用层编排
- `smart_filer/application/services/suggestion_explainer.py`：建议结果说明与规则依据整理
- `tests/test_step5_domain_models.py`：步骤5测试
- `tests/test_step6_rules_document_loader.py`：步骤6测试
- `tests/test_step7_rule_document_parser.py`：步骤7测试
- `tests/test_step8_install_path_hard_rules.py`：步骤8测试
- `tests/test_step9_llm_models.py`：步骤9测试
- `tests/test_step10_siliconflow_adapter.py`：步骤10测试
- `tests/test_step11_prompt_builder.py`：步骤11测试
- `tests/test_step12_llm_response_service.py`：步骤12测试
- `tests/test_step13_install_path_suggestion_use_case.py`：步骤13测试
- `tests/test_step14_suggestion_explainer.py`：步骤14测试
- `tests/test_step15_cli_root.py`：步骤15测试
- `tests/test_step16_cli_suggest_install_path_command.py`：步骤16测试

## 11. 完整数据库 Schema（全量草案，尚未实现）

> 说明：当前版本尚未接入 SQLite 持久化；以下为后续阶段将落地的完整 schema 草案。

```sql
CREATE TABLE IF NOT EXISTS scanned_directories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  path TEXT NOT NULL UNIQUE,
  path_hash TEXT NOT NULL UNIQUE,
  last_scanned_at TEXT,
  scan_status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS routing_rules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  rule_key TEXT NOT NULL UNIQUE,
  rule_type TEXT NOT NULL,
  source_document TEXT NOT NULL,
  source_version TEXT,
  priority INTEGER NOT NULL DEFAULT 100,
  is_active INTEGER NOT NULL DEFAULT 1,
  rule_content_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS file_processing_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_name TEXT NOT NULL,
  original_path TEXT NOT NULL,
  file_extension TEXT,
  file_size_bytes INTEGER,
  detected_category TEXT,
  suggested_path TEXT NOT NULL,
  suggested_name TEXT,
  final_action TEXT NOT NULL DEFAULT 'suggest_only',
  decision_source TEXT NOT NULL,
  needs_confirmation INTEGER NOT NULL DEFAULT 1,
  fallback_used INTEGER NOT NULL DEFAULT 0,
  confidence REAL,
  reason TEXT,
  rule_basis_json TEXT,
  llm_raw_output TEXT,
  processed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS installed_software (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  normalized_name TEXT NOT NULL,
  display_name TEXT,
  version TEXT,
  vendor TEXT,
  install_path TEXT,
  executable_path TEXT,
  source TEXT NOT NULL DEFAULT 'system_scan',
  detected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(normalized_name, install_path)
);

CREATE TABLE IF NOT EXISTS software_capability_tags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  capability_tag TEXT NOT NULL UNIQUE,
  description TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS software_capability_mapping (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  software_id INTEGER NOT NULL,
  capability_tag_id INTEGER NOT NULL,
  confidence REAL NOT NULL DEFAULT 1.0,
  source TEXT NOT NULL DEFAULT 'manual',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(software_id, capability_tag_id),
  FOREIGN KEY (software_id) REFERENCES installed_software(id),
  FOREIGN KEY (capability_tag_id) REFERENCES software_capability_tags(id)
);

CREATE TABLE IF NOT EXISTS llm_decision_audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id TEXT NOT NULL UNIQUE,
  provider TEXT NOT NULL DEFAULT 'siliconflow',
  model_id TEXT,
  prompt_text TEXT NOT NULL,
  response_text TEXT,
  response_json TEXT,
  parse_status TEXT NOT NULL,
  error_message TEXT,
  latency_ms INTEGER,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS operation_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  level TEXT NOT NULL,
  module TEXT NOT NULL,
  event_type TEXT NOT NULL,
  message TEXT NOT NULL,
  context_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scanned_directories_status
ON scanned_directories(scan_status);

CREATE INDEX IF NOT EXISTS idx_file_processing_history_processed_at
ON file_processing_history(processed_at);

CREATE INDEX IF NOT EXISTS idx_file_processing_history_detected_category
ON file_processing_history(detected_category);

CREATE INDEX IF NOT EXISTS idx_installed_software_normalized_name
ON installed_software(normalized_name);

CREATE INDEX IF NOT EXISTS idx_llm_decision_audit_created_at
ON llm_decision_audit(created_at);

CREATE INDEX IF NOT EXISTS idx_operation_log_level_created_at
ON operation_log(level, created_at);
```
