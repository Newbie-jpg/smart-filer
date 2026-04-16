# smart-filer 开发进度

## 2026-04-15

### 已完成里程碑

1. **步骤1：项目骨架与基础导入**
- 新建分层目录：`smart_filer/cli`、`smart_filer/application`、`smart_filer/domain`、`smart_filer/infrastructure`、`tests`
- 补齐包初始化文件 `__init__.py`
- 新增结构与导入测试：`tests/test_step1_project_structure.py`

2. **步骤2：项目元数据与依赖声明**
- 新建 `pyproject.toml`，声明 Python 版本与首版依赖
- 新建依赖安装规范文档：`docs/dependency-installation.md`
- 新增步骤2校验测试：`tests/test_step2_project_metadata.py`

3. **步骤3：全局配置模块**
- 新建 `smart_filer/config.py`
- 增加配置项（规则文档路径、SiliconFlow API 配置、日志目录、LLM 开关、超时、回退确认）
- 支持环境变量覆盖（前缀 `SMART_FILER_`）
- 增加关键配置校验（LLM 启用时 API key / model 必填）
- 新增配置测试：`tests/test_step3_config.py`

4. **步骤4：日志初始化模块**
- 新建统一日志入口：`smart_filer/infrastructure/logging_setup.py`
- 支持统一格式、文件+控制台双通道输出
- 支持重复初始化防重（避免重复 handler）
- 新增日志测试：`tests/test_step4_logging_setup.py`

## 2026-04-16

### 本次完成（步骤5-8）

5. **步骤5：领域模型定义**
- 新建 `smart_filer/domain/models/` 并拆分领域模型：
  - `software_category.py`：软件类别枚举
  - `rule_metadata.py`：规则来源、规则优先级、回退状态、规则依据对象
  - `install_suggestion.py`：安装建议结果模型（字段约束+一致性校验）
- 更新 `smart_filer/domain/__init__.py` 暴露核心领域对象
- 新增测试：`tests/test_step5_domain_models.py`
  - 覆盖枚举值/非法值
  - 覆盖序列化/反序列化
  - 覆盖字段约束与回退状态一致性校验

6. **步骤6：规则文档加载器**
- 新建 `smart_filer/infrastructure/rules/document_loader.py`
- 仅负责文档读取，不承载解析业务
- 明确异常处理：
  - 文档不存在
  - 路径非文件
  - 编码异常（非 UTF-8）
  - 空文件
- 新增 `smart_filer/infrastructure/rules/__init__.py`
- 新增测试：`tests/test_step6_rules_document_loader.py`
  - 验证可读取 `文件结构.md`
  - 验证 UTF-8 中文内容读取正确
  - 验证缺失/空文件/编码异常抛出明确错误

### 测试结果

- 执行命令：
  - `uv run pytest -s tests/test_step1_project_structure.py tests/test_step2_project_metadata.py tests/test_step3_config.py tests/test_step4_logging_setup.py tests/test_step5_domain_models.py tests/test_step6_rules_document_loader.py tests/test_step7_rule_document_parser.py tests/test_step8_install_path_hard_rules.py`
- 结果：`31 passed`
- 测试环境：Python `3.12.13`

### 本次新增（步骤7-8）

7. **步骤7：规则文档解析器**
- 新建 `smart_filer/infrastructure/rules/document_parser.py`
- 解析 `文件结构.md` 到中间规则对象 `ParsedInstallRules`：
  - 提取 `D:` 盘优先原则
  - 提取“软件不建议安装到 `S:` 盘”约束
  - 提取软件类别到 `D:\xx_xxx` 安装目录映射
- 解析器在遇到未知映射格式时记录 `warnings`，避免静默忽略
- 新增测试：`tests/test_step7_rule_document_parser.py`

8. **步骤8：安装位置硬规则服务**
- 新建 `smart_filer/domain/services/install_path_hard_rules.py`
- 实现硬规则覆盖逻辑：
  - 若类别存在映射，优先使用规则映射路径
  - 若上游给出 `S:` 盘路径，改写到 `D:` 盘保守路径
  - 若给出非 `D:` 盘路径（如 `C:`），改写到 `D:` 盘保守路径
  - 若无类别映射但已是 `D:` 路径，允许保留
- 新增测试：`tests/test_step8_install_path_hard_rules.py`

### 本次新增（步骤9-10）

9. **步骤9：定义 LLM 请求与响应模型**
- 新建 `smart_filer/domain/models/llm_models.py`
- 定义 `LLMInstallPathRequest`：
  - `software_name`
  - `rule_summary`
  - `aliases`（可选）
  - `context`（可选）
- 定义 `LLMInstallPathResponse`：
  - `category`（映射到 `software_category`）
  - `suggested_path`（映射到 `suggested_install_path`）
  - `reason`
  - `confidence`
- 增加列表项非空校验与置信度范围校验
- 更新导出：
  - `smart_filer/domain/models/__init__.py`
  - `smart_filer/domain/__init__.py`
- 新增测试：`tests/test_step9_llm_models.py`
  - 覆盖字段完整性、别名映射、缺失字段拒绝、非法列表项拒绝

10. **步骤10：实现 SiliconFlow provider adapter**
- 新建 provider 目录与导出：
  - `smart_filer/infrastructure/providers/__init__.py`
  - `smart_filer/infrastructure/providers/siliconflow_adapter.py`
- 新增 `SiliconFlowAdapter`，封装 OpenAI 兼容调用：
  - 支持 `base_url`、`model_id`、`timeout` 配置
  - 支持从 `AppSettings` 构造适配器
  - 输出 `SiliconFlowAdapterResult`，保留结构化响应与原始响应文本
- 新增内部错误语义：
  - `SiliconFlowAdapterError`
  - `SiliconFlowTimeoutError`
  - `SiliconFlowResponseError`
- 新增测试：`tests/test_step10_siliconflow_adapter.py`
  - 覆盖请求参数组装
  - 覆盖 base URL / model ID / timeout 配置透传
  - 覆盖超时、空响应、非 JSON 响应错误包装

### 本次新增（步骤11-12）

11. **步骤11：实现提示词构建器**
- 新建 `smart_filer/infrastructure/providers/prompt_builder.py`
- 新增 `InstallPathPromptBuilder`，专责将 `LLMInstallPathRequest` 构建为稳定消息列表
  - 明确 system prompt 中的结构化输出要求（JSON + 必填字段）
  - 在 user prompt 中显式注入软件名、别名、上下文、规则摘要
  - 保持规则摘要顺序稳定，便于后续可重复测试
- 重构 `smart_filer/infrastructure/providers/siliconflow_adapter.py`
  - 移除适配器内嵌 prompt 拼装逻辑
  - 通过注入式 `prompt_builder` 调用，完成职责解耦
- 更新导出：
  - `smart_filer/infrastructure/providers/__init__.py`
- 新增测试：`tests/test_step11_prompt_builder.py`
  - 覆盖提示词输入完整性
  - 覆盖规则摘要顺序稳定性

12. **步骤12：实现 LLM 响应解析与回退服务**
- 新建应用层服务：
  - `smart_filer/application/services/llm_response_service.py`
  - `smart_filer/application/services/__init__.py`
- 新增 `build_install_suggestion_from_llm`：
  - 将 provider 返回统一转换为 `InstallSuggestion`
  - 对合法结构化响应走正常路径（含硬规则校验）
  - 对异常场景统一进入回退策略并要求人工确认
- 回退覆盖场景：
  - LLM 调用失败（超时/请求错误）
  - 非法结构化结果（如非 JSON、字段缺失，经 adapter 归一为响应错误）
  - 低置信度
  - 非法安装路径（如 `S:` 盘或非 `D:` 盘）
  - 类别与规则映射冲突
- 新增测试：`tests/test_step12_llm_response_service.py`
  - 覆盖合法结构化响应
  - 覆盖非法 JSON
  - 覆盖字段缺失
  - 覆盖低置信度
  - 覆盖 `S:` 盘非法路径
  - 覆盖 LLM 完全失败

### 本次新增（步骤13-14）

13. **步骤13：实现软件安装位置建议用例**
- 新建应用层用例模块：
  - `smart_filer/application/use_cases/install_path_suggestion.py`
  - `smart_filer/application/use_cases/__init__.py`
- 新增 `SuggestInstallPathUseCase`，完成首版主编排：
  - 输入软件名（可选别名与上下文）
  - 加载规则文档并解析为 `ParsedInstallRules`
  - 组装结构化 `LLMInstallPathRequest`（包含规则摘要）
  - 调用 provider 分类
  - 统一走 `build_install_suggestion_from_llm` 做硬规则校验与回退
  - 输出最终 `InstallSuggestion`
- 支持关键保护逻辑：
  - LLM 未启用时直接回退为保守建议
  - 适配器初始化失败时回退
  - LLM 请求异常时回退
  - 低置信度阈值参数可配置
- 更新导出：
  - `smart_filer/application/__init__.py`
- 新增测试：`tests/test_step13_install_path_suggestion_use_case.py`
  - 覆盖工程类、办公效率类、媒体设计类、系统工具类、游戏平台类
  - 覆盖“无法可靠分类”回退
  - 验证结果始终 `needs_confirmation = true`

14. **步骤14：实现结果说明与规则依据整理**
- 新建说明整理模块：
  - `smart_filer/application/services/suggestion_explainer.py`
- 新增 `SuggestionExplanation` 与 `build_suggestion_explanation`：
  - 输出“为什么建议该路径”的稳定说明文本
  - 输出可读、可排序的规则依据列表（含来源与优先级）
  - 输出回退状态说明（含回退触发原因）
- 更新导出：
  - `smart_filer/application/services/__init__.py`
- 新增测试：`tests/test_step14_suggestion_explainer.py`
  - 验证说明文本稳定、可读
  - 验证规则依据排序稳定
  - 验证回退场景下原因说明不缺失

### 最新测试结果

- 执行命令：
  - `uv run pytest -s tests`
- 结果：`56 passed`
- 测试环境：Python `3.12.13`

### 本次新增（步骤15-16）

15. **步骤15：建立 CLI 根入口**
- 新建 CLI 根应用与进程入口：
  - `smart_filer/cli/app.py`
  - `smart_filer/main.py`
- 新建统一输出模块：
  - `smart_filer/cli/output.py`
- 新建命令包初始化：
  - `smart_filer/cli/commands/__init__.py`
- 更新 `smart_filer/cli/__init__.py` 暴露 `app` / `run_cli`
- 更新 `pyproject.toml`：
  - 新增脚本入口 `smart-filer = "smart_filer.main:main"`
- 行为落地：
  - 根命令可启动并显示帮助
  - `--help` 可显示命令列表
  - 顶层未知异常统一友好处理并返回非零退出码
- 新增测试：
  - `tests/test_step15_cli_root.py`
  - 覆盖根命令启动、帮助信息、顶层异常处理、退出码透传

16. **步骤16：实现软件安装位置建议命令**
- 新建命令实现：
  - `smart_filer/cli/commands/suggest_install_path.py`
- 新增命令：
  - `suggest-install-path "OBS Studio"`
- 命令编排：
  - 读取配置并初始化日志
  - 调用 `SuggestInstallPathUseCase`
  - 调用 `build_suggestion_explanation`
  - 输出结构化 JSON（`suggestion` + `explanation`）
- 错误与边界处理：
  - 空输入直接友好报错
  - 用例异常时返回错误并退出
  - 不可靠分类与 LLM 回退场景稳定输出 fallback 结果
- 新增测试：
  - `tests/test_step16_cli_suggest_install_path_command.py`
  - 覆盖正常输入、空输入、无法分类、LLM 回退

### 最新测试结果（步骤1-16）

- 执行命令：
  - `uv run pytest -s tests/test_step15_cli_root.py tests/test_step16_cli_suggest_install_path_command.py`
  - `uv run pytest -s tests`
- 结果：
  - 步骤15-16专项：`8 passed`
  - 全量：`64 passed`
- 测试环境：Python `3.12.13`

### 下一步建议

- 进入步骤17：补齐 CLI 到应用层的集成测试（含规则文档缺失与规则重载生效场景）
