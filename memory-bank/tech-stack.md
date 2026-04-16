# smart-filer 技术栈建议

## 结论

`smart-filer` 最适合采用一套 **Python 单体 CLI 技术栈**：

- **语言**：Python 3.12
- **项目与依赖管理**：`uv`
- **CLI 框架**：`Typer`
- **数据模型与配置**：`Pydantic v2` + `pydantic-settings`
- **本地数据库**：SQLite
- **ORM / 查询层**：SQLAlchemy 2.0
- **LLM 接入**：OpenAI 官方 Python SDK，外面包一层 provider adapter
- **文件监听**：`watchdog`
- **文档解析**：`pypdf`、`python-docx`
- **Windows 安装包识别**：`pefile` + Windows 注册表读取
- **日志**：Python 标准库 `logging`
- **测试**：`pytest`
- **打包发布**：`PyInstaller`

这是当前最简单、最稳健、最适合本项目首版落地的方案。

---

## 为什么这套最合适

### 1. Python 最匹配这个项目的问题类型

`smart-filer` 的核心不是高并发 Web 服务，而是：

- 本地文件系统扫描
- PDF / Word / 安装包解析
- Windows 路径与注册表读取
- 调用 LLM API
- 执行文件移动、重命名、归档

这类任务 Python 的生态最成熟，开发速度也最快。

### 2. 单体 CLI 比前后端分离更稳

首版真正要解决的是“规则解析 + 文件识别 + LLM 决策 + 本地执行”，不是 UI。

因此建议采用：

- 一个 Python 应用
- 一个本地 SQLite 数据库
- 一套命令行入口

先把核心链路跑通，后续如果需要桌面端，再在现有核心上加 GUI，而不是一开始就做 Electron 或前后端分离。

### 3. SQLite 足够且更可靠

这个项目是单机本地工具，数据主要是：

- 文件索引
- 软件清单
- 路由历史
- 用户确认记录

SQLite 不需要单独安装服务，备份简单，调试方便，稳定性也足够高。

### 4. Typer 很适合做首版交互

首版可以快速做出下面这种命令：

```bash
smart-filer suggest "C:\Users\me\Downloads\abc.pdf"
smart-filer route "C:\Users\me\Downloads\setup.exe" --apply
smart-filer check-software "录屏"
smart-filer watch "C:\Users\me\Downloads"
```

这比先做桌面 GUI 更快，也更容易测试和迭代。

---

## 推荐架构

### 架构风格

采用 **本地单体应用 + 分层模块设计**：

1. `cli`
2. `application`
3. `domain`
4. `infrastructure`

### 分层说明

- `cli`
  - 接收命令参数
  - 展示建议结果
  - 请求用户确认
- `application`
  - 编排“扫描 -> 提取 -> LLM 判断 -> 规则校验 -> 写入索引 -> 执行”
- `domain`
  - 放置路由规则、命名规则、软件类别、决策对象
- `infrastructure`
  - 文件系统、SQLite、OpenAI API、PDF/Word 解析、Windows 注册表访问

---

## 技术栈明细

| 层 | 推荐 | 原因 |
| --- | --- | --- |
| 语言 | Python 3.12 | 标准库强、Windows 友好、文件处理生态成熟 |
| 依赖管理 | uv | 比 `pip + venv` 更快、更简单，适合新项目 |
| CLI | Typer | 上手快、类型友好、非常适合工具型项目 |
| 配置与模型 | Pydantic v2 | 做 LLM 输入输出、配置校验很稳 |
| 本地存储 | SQLite | 零运维、稳健、适合单机工具 |
| 数据访问 | SQLAlchemy 2.0 | 比直接拼 SQL 更可维护，后续扩展也稳 |
| 文件监听 | watchdog | 做下载目录监听很合适 |
| PDF 解析 | pypdf | 轻量、成熟、足够满足首版摘要提取 |
| Word 解析 | python-docx | 对 `.docx` 支持稳定 |
| EXE 信息识别 | pefile | 适合读取 PE 元数据 |
| LLM SDK | OpenAI Python SDK | 官方维护，接口稳定 |
| 日志 | logging | 标准库足够，依赖更少 |
| 测试 | pytest | Python 事实标准 |
| 打包 | PyInstaller | 方便交付给 Windows 用户 |

---

## 建议目录结构

```text
smart-filer/
├─ pyproject.toml
├─ README.md
├─ smart_filer/
│  ├─ cli/
│  ├─ application/
│  ├─ domain/
│  ├─ infrastructure/
│  ├─ config.py
│  └─ main.py
├─ tests/
├─ data/
│  └─ smart_filer.db
└─ docs/
```

---

## 首版建议引入的关键依赖

```toml
[project]
dependencies = [
  "typer>=0.12",
  "pydantic>=2.8",
  "pydantic-settings>=2.4",
  "sqlalchemy>=2.0",
  "openai>=1.0",
  "watchdog>=4.0",
  "pypdf>=4.0",
  "python-docx>=1.1",
  "pefile>=2024.8.26",
]
```

开发依赖：

```toml
[dependency-groups]
dev = [
  "pytest>=8.0",
  "ruff>=0.6",
]
```

---

## 不建议首版采用的方案

### 不建议：Node.js / Electron 作为主栈

原因：

- 本地文件解析和 Windows 系统信息读取没有 Python 顺手
- Electron 对首版来说偏重
- 会把重点从“功能能不能跑通”转移到“桌面应用壳子”

### 不建议：PostgreSQL

原因：

- 单机工具没有必要引入独立数据库服务
- 增加安装和维护成本

### 不建议：FastAPI 作为首版核心入口

原因：

- 这个项目本质上不是 Web API 优先
- 首版 CLI 更直接

说明：

- 如果后续要做本地 GUI、Web 控制台或插件化，再在现有核心外面加 FastAPI 很自然

### 不建议：LangChain 等重编排框架

原因：

- 首版需求并不复杂
- 直接自己封装 prompt 和 JSON 输出更稳、更可控
- 少一层抽象，排错更容易

---

## 最终推荐版本

如果只保留一句话，我建议你这样定：

> **Python 3.12 + uv + Typer + Pydantic + SQLite + SQLAlchemy + OpenAI SDK + watchdog + pytest**

这套技术栈足够简单，能很快做出 MVP，同时也足够稳健，不会在项目变大后很快推倒重来。

---

## 参考资料

- Python 官方文档：https://docs.python.org/3/
- uv 官方文档：https://docs.astral.sh/uv/
- Typer 官方文档：https://typer.tiangolo.com/
- Pydantic 官方文档：https://docs.pydantic.dev/latest/
- SQLAlchemy 官方文档：https://docs.sqlalchemy.org/
- OpenAI Python SDK 官方文档：https://github.com/openai/openai-python
- watchdog 文档：https://python-watchdog.readthedocs.io/
- pypdf 文档：https://pypdf.readthedocs.io/
- pytest 官方文档：https://docs.pytest.org/
- PyInstaller 官方文档：https://pyinstaller.org/
