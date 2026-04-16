# smart-filer 架构说明（当前实现）

## 1. 当前架构状态（截至 2026-04-16）

- 本仓库已完成实施计划步骤 1-8。
- 当前处于“规则系统与硬规则校验完成”阶段：
  - 已完成目录分层、依赖声明、配置加载、日志初始化。
  - 已完成领域模型定义（软件类别、规则元数据、安装建议结果）。
  - 已完成规则文档加载器（仅负责读取文本，和业务解析解耦）。
  - 已完成规则文档解析器（提取 D 盘优先、S 盘约束、类别路径映射）。
  - 已完成安装路径硬规则服务（映射优先、非法路径纠正）。
- 核心业务编排尚未完成：LLM 适配、建议用例、CLI 命令仍待实现。

## 2. 分层与依赖方向

- 依赖方向遵循：
  - `cli -> application -> domain`
  - `application -> infrastructure`
  - `infrastructure -> domain`
- 当前关键实现：
  - `smart_filer/config.py`：跨层共享配置入口
  - `smart_filer/infrastructure/logging_setup.py`：统一日志初始化入口
  - `smart_filer/domain/models/*`：领域模型
  - `smart_filer/infrastructure/rules/document_loader.py`：规则文档读取适配器
  - `smart_filer/infrastructure/rules/document_parser.py`：规则文档解析器
  - `smart_filer/domain/services/install_path_hard_rules.py`：安装路径硬规则服务

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

## 5. 测试覆盖概览

- `tests/test_step1_project_structure.py`：分层目录与包导入
- `tests/test_step2_project_metadata.py`：依赖声明与安装规则文档约束
- `tests/test_step3_config.py`：配置默认值、覆盖、关键字段校验
- `tests/test_step4_logging_setup.py`：日志初始化与幂等性
- `tests/test_step5_domain_models.py`：领域模型校验、枚举非法值、序列化反序列化
- `tests/test_step6_rules_document_loader.py`：规则文档读取、中文读取、异常场景
- `tests/test_step7_rule_document_parser.py`：规则提取（D盘优先/S盘约束/类别映射）与未知格式告警
- `tests/test_step8_install_path_hard_rules.py`：硬规则覆盖、S盘纠正、非D盘纠正与保留合法D盘路径

最新验证结果：步骤1-8测试总计 `31 passed`。

## 6. 文件职责（当前实现）

- `smart_filer/config.py`：全局配置定义与读取
- `smart_filer/infrastructure/logging_setup.py`：日志初始化
- `smart_filer/domain/models/software_category.py`：软件类别枚举
- `smart_filer/domain/models/rule_metadata.py`：规则来源/优先级/回退状态与规则依据对象
- `smart_filer/domain/models/install_suggestion.py`：安装建议结果模型
- `smart_filer/domain/models/parsed_rules.py`：规则文档解析后的中间表示
- `smart_filer/infrastructure/rules/document_loader.py`：规则文档原文加载
- `smart_filer/infrastructure/rules/document_parser.py`：规则文档解析器
- `smart_filer/domain/services/install_path_hard_rules.py`：安装路径硬规则服务
- `tests/test_step5_domain_models.py`：步骤5测试
- `tests/test_step6_rules_document_loader.py`：步骤6测试
- `tests/test_step7_rule_document_parser.py`：步骤7测试
- `tests/test_step8_install_path_hard_rules.py`：步骤8测试

## 7. 完整数据库 Schema（全量草案，尚未实现）

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
