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

### 下一步建议

- 进入步骤9：定义 LLM 请求与响应模型
