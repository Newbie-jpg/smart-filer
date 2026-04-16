# 依赖安装与环境落点规范（步骤二）

本文件定义本项目在首版阶段的依赖安装规则，确保与 `文件结构.md` 的盘符规划一致。

## 1) 项目源码位置（Source）

- 项目源码仓库保留在工作目录：`S:\001_Workspace\smart-filer`
- 不在 `D:` 盘存放源码副本作为主工作目录

## 2) Python 与虚拟环境位置（Interpreter / Venv）

- Python 解释器与虚拟环境统一落在：`D:\10_Environments\Python`
- 推荐项目虚拟环境路径：`D:\10_Environments\Python\venvs\smart-filer`
- 不要将可迁移虚拟环境创建在 `S:` 盘数据目录

### 当前开发机实际落点（已发生偏离）

当前开发机已将 venv 放在仓库目录内（例如仓库根目录下的 `.venv`），这与上面的推荐落点不同。

为避免后续开发者误用系统 Python 或其他环境，建议在仓库根目录用下面命令自检实际解释器路径：

```powershell
uv run python -c "import sys; print(sys.version); print(sys.executable)"
```

## 3) 缓存与临时文件位置（Cache / Temp）

- `uv` 缓存统一落在：`D:\00_Temp_Cache\uv`
- 临时构建与下载缓存遵循 `D:\00_Temp_Cache` 体系

## 4) `uv` 建议执行方式（PowerShell）

```powershell
$env:UV_PROJECT_ENVIRONMENT = "D:\10_Environments\Python\venvs\smart-filer"
$env:UV_CACHE_DIR = "D:\00_Temp_Cache\uv"
uv sync --python 3.12 --group dev
```

可选：如果由 `uv` 管理 Python 安装目录，可设置：

```powershell
$env:UV_PYTHON_INSTALL_DIR = "D:\10_Environments\Python\interpreters"
```

## 5) 禁止项

- 不引入 FastAPI 作为首版主入口
- 不引入 Electron / Node.js 作为主技术栈
- 不引入 PostgreSQL
- 不引入 LangChain 等重编排框架
