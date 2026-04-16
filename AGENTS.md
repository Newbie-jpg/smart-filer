# smart-filer 项目规则

本文件定义 `smart-filer` 仓库的默认开发规则，适用于整个项目。

## 1. 项目定位

- `smart-filer` 是一个面向 Windows 本地环境的文件智能路由工具。
- 首版以 **本地单体 CLI 应用** 交付，不以 Web 服务、桌面壳或前后端分离为目标。
- 核心目标是打通“规则解析 -> 文件识别 -> LLM 决策 -> 规则校验 -> 本地执行 -> 日志/索引写入”链路。
- 产品定位是“智能建议与辅助执行”，不是完全替代人工判断。

## 2. 技术栈约束

- Python 版本：`Python 3.12`
- 依赖与环境管理：`uv`
- CLI：`Typer`
- 配置与数据模型：`Pydantic v2` + `pydantic-settings`
- 本地存储：`SQLite`
- 数据访问：`SQLAlchemy 2.0`
- LLM 接入：`OpenAI Python SDK`，并在项目内封装 provider adapter
- 文件监听：`watchdog`
- PDF 解析：`pypdf`
- Word 解析：`python-docx`
- Windows 安装包识别：`pefile` + Windows 注册表读取
- 日志：标准库 `logging`
- 测试：`pytest`
- 打包：`PyInstaller`

## 3. 首版明确不采用

- 不引入 `FastAPI` 作为首版主入口
- 不引入 `Electron` / Node.js 作为主技术栈
- 不引入 `PostgreSQL`
- 不引入 `LangChain` 等重编排框架

如需偏离以上约束，必须先更新设计文档与本规则。

## 4. 架构规则

项目必须采用分层模块设计，基础目录建议如下：

```text
smart_filer/
├─ cli/
├─ application/
├─ domain/
├─ infrastructure/
├─ config.py
└─ main.py
```

各层职责必须保持清晰：

- `cli`
  - 只负责命令定义、参数接收、结果展示、用户确认
  - 不承载核心业务规则
- `application`
  - 负责编排用例流程
  - 串联分析、决策、校验、索引、执行
- `domain`
  - 放纯业务概念与规则
  - 包含路由规则、命名规则、分类模型、决策对象
  - 不依赖具体基础设施实现
- `infrastructure`
  - 放文件系统、SQLite、OpenAI、文档解析、Windows 集成等适配器
  - 不写业务决策本身

## 5. 模块化强制要求

- 必须优先拆分为多个小模块，避免单一“大而全”文件。
- 禁止把 CLI、业务编排、领域规则、基础设施适配、数据模型混写在同一个文件。
- 新功能开发时，优先新增模块文件，而不是持续堆叠到已有大文件。
- 单个文件若开始同时承担多个职责，必须拆分。
- 单个文件若明显变成“入口 + 规则 + 持久化 + 外部调用”的混合体，必须重构。
- 除极小型数据结构文件外，优先“一类职责一个模块”。

推荐拆分粒度：

- `cli/commands/*.py`：按命令拆分
- `application/services/*.py` 或 `application/use_cases/*.py`：按用例拆分
- `domain/models/*.py`、`domain/rules/*.py`、`domain/services/*.py`：按领域概念拆分
- `infrastructure/repositories/*.py`、`infrastructure/parsers/*.py`、`infrastructure/providers/*.py`、`infrastructure/system/*.py`：按外部能力拆分

## 6. 依赖方向规则

- 允许：`cli -> application -> domain`
- 允许：`application -> domain`
- 允许：`application -> infrastructure`
- 允许：`infrastructure -> domain`
- 禁止：`domain -> cli`
- 禁止：`domain -> infrastructure` 中的具体 SDK/ORM/系统实现
- 禁止：`cli` 直接编排完整业务流程或直接承载复杂规则

如需跨层协作，优先通过接口、DTO、领域对象或应用层服务完成。

## 7. 业务实现规则

- 所有路由判断必须优先服从本地硬规则，再结合 LLM 输出。
- LLM 输出必须为结构化结果，禁止依赖随意文本段落作为核心决策输入。
- 高风险操作必须保留人工确认，尤其是：
  - 文件移动
  - 文件重命名
  - 安装程序执行
  - 归档或删除建议
- 默认支持两种模式：
  - 建议模式：仅输出建议
  - 执行模式：用户确认后执行
- 规则变更后，系统应能重新加载并生效。
- 默认本地优先，敏感文件优先只上传摘要，不上传全文。

## 8. MVP 优先级

首版优先完成以下能力：

1. 读取并解析规则文档
2. 识别 `pdf`、`docx`、`exe`、`msi`、`zip`
3. 输出推荐路径与推荐命名
4. 提供建议模式
5. 记录处理日志
6. 支持软件存在性检查
7. 在本机缺失软件时给出推荐和安装位置建议

非 MVP 能力不要提前扩张实现复杂度。

## 9. 数据与输出规则

- 路由决策结果应尽量标准化为结构化对象。
- LLM 输出建议采用 JSON，至少包含：
  - `category`
  - `suggested_path`
  - `suggested_name`
  - `reason`
  - `confidence`
  - `needs_confirmation`
  - `software_recommendation`
- 本地索引至少覆盖：
  - 已扫描目录结构
  - 文件处理历史
  - 已安装软件清单
  - 软件能力标签映射

## 10. 代码风格规则

- 保持实现简单、可读、可维护。
- 优先使用小函数、小类、小模块。
- 一个函数只做一件事；一个模块聚焦一类职责。
- 避免“万能工具类”“万能 service”“万能 utils.py”。
- 公共能力应按语义命名，不用含糊命名。
- 优先显式数据模型，避免无结构 `dict` 在系统内层层透传。
- 配置、路径规则、常量、提示词模板不得散落在单个超大文件中。

## 11. 测试与质量规则

- 使用 `pytest` 编写测试。
- 新增业务规则时，优先补对应单元测试。
- 优先测试：
  - 规则解析
  - 路由决策校验
  - 命名规范化
  - 软件存在性检查
- 测试也应模块化，不写单个超大测试文件覆盖全部场景。

## 12. 文档同步规则

- 影响架构、模块边界、关键流程、技术选型的变更，必须同步更新相关文档。
- 若实现与 `tech-stack.md` 或 `smart-filer-design-document.md` 冲突，应先修正文档或先征得确认。

## 13. 实施原则总结

- 先做 CLI，后谈 GUI。
- 先做模块边界，后加功能堆叠。
- 先做硬规则约束，后接 LLM 决策。
- 先做建议模式，后做执行模式。
- 始终保持多文件、模块化、可演进，避免单文件架构。

# IMPORTANT:
# Always read memory-bank/@architecture.md before writing any code. Include entire database schema.
# Always read memory-bank/@smart-filer-design-document.md before writing any code.
# After adding a major feature or completing a milestone, update memory-bank/@architecture.md.