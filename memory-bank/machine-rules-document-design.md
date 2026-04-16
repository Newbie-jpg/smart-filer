# smart-filer 机器优先规则文档设计

## 1. 文档定位

- 文档名称：`machine-rules-document-design.md`
- 状态：设计中 / 未落地到当前解析器
- 生效范围：下一版规则文档规范
- 关联文档：
  - `memory-bank/smart-filer-design-document.md`
  - `memory-bank/architecture.md`
  - `文件结构.md`

本设计文档用于定义一套“机器优先”的规则文档规范，供 `smart-filer` 后续替换当前偏自然语言的 `文件结构.md` 解析方式。

当前 `文件结构.md` 更偏向人类阅读，适合作为说明文档，但不适合作为唯一规则源。下一版规则文档需要优先服务程序解析与 LLM 提示构造，减少歧义、隐含推断和上下文依赖。

## 2. 设计背景

当前规则文档存在以下问题：

- 规则以自然语言叙述为主，程序需要依赖关键词猜测类别。
- 同一软件可能命中多个语义相近类别，缺少显式冲突解法。
- “软件安装位置”和“软件数据位置”容易在描述上混淆。
- 软件特例规则常埋在长段说明中，难以稳定提取。
- 文档面向人类可读性优化过多，导致模型与解析器对边界的理解不稳定。

下一版规则文档的目标不是替代说明文档，而是提供一份可被程序稳定消费的规则源。

## 3. 总体目标

下一版规则文档必须满足以下目标：

1. 程序可稳定解析，不依赖模糊语义推断。
2. 同一软件在同一规则版本下应得到唯一、可复现的分类结果。
3. 软件类别、默认路径、特例路径、禁止路径都必须显式声明。
4. 新增软件特例时，优先修改文档，不要求同步修改解析器代码。
5. 文档应保持 Markdown 外壳下的结构化规则块形式，兼顾版本管理与人工审阅。

## 4. 明确边界

### 4.1 本设计包含

- 软件类别定义
- 默认安装路径
- 软件特例覆盖规则
- 禁止安装路径
- 冲突解决顺序
- 文档版本与校验要求

### 4.2 本设计不包含

- 云同步目录设计
- OneDrive、Dropbox、iCloud 等同步策略
- 同步盘路径映射
- 远端备份和跨设备同步规则

说明：

- 新版规则文档默认不建模任何云同步概念。
- 规则字段中不得出现 `sync_path`、`cloud_path`、`vault_sync` 等同步相关字段。
- 若未来需要同步能力，应单独设计新的文档规范，而不是混入本规则文档。

## 5. 核心设计原则

### 5.1 机器优先

- 文档首先为程序解析服务，其次才是人工阅读。
- 规则必须能脱离长段自然语言单独成立。

### 5.2 单一职责

- 一个字段只表达一个语义。
- “软件安装路径”与“软件数据路径”必须拆开。

### 5.3 显式优先于隐式

- 所有优先级、冲突关系、特例覆盖都必须显式写出。
- 不允许依赖“通常”“一般”“建议优先”等模糊表述充当机器规则。

### 5.4 可扩展但不开放

- 文档支持扩展字段，但核心字段必须受控。
- 受控枚举之外不允许自由发明新类别名。

### 5.5 本地优先

- 下一版规则文档只讨论本地路径与本地目录角色。
- 所有路径均以 Windows 本地绝对路径表达。

## 6. 必备结构

下一版规则文档建议采用“Markdown 标题 + 单个 YAML 规则块”的形式。

文档中必须包含以下顶层结构：

1. `metadata`
2. `global_rules`
3. `categories`
4. `software_overrides`
5. `conflict_resolution`
6. `validation_examples`

### 6.1 metadata

必须字段：

- `rules_version`
- `document_type`
- `document_status`
- `platform`
- `path_style`

约束：

- `rules_version` 必须为整数。
- `document_type` 必须固定为 `smart_filer_machine_rules`。
- `platform` 当前固定为 `windows`。
- `path_style` 当前固定为 `windows_absolute`。

### 6.2 global_rules

必须字段：

- `preferred_install_drive`
- `forbidden_install_roots`
- `fallback_install_path`
- `allow_only_local_paths`

约束：

- `preferred_install_drive` 当前应为 `D:`
- `forbidden_install_roots` 必须至少包含 `S:\`
- `fallback_install_path` 必须是合法的 `D:\` 路径
- `allow_only_local_paths` 必须为 `true`

### 6.3 categories

必须为数组。每个类别对象必须包含：

- `id`
- `display_name`
- `priority`
- `definition`
- `includes`
- `excludes`
- `default_install_path`
- `allowed_install_paths`

约束：

- `id` 必须属于受控枚举：
  - `development_environment`
  - `engineering`
  - `productivity`
  - `media_design`
  - `system_utilities`
  - `games_entertain`
- `priority` 必须为整数。
- `default_install_path` 必须同时出现在 `allowed_install_paths` 中。
- `includes` 和 `excludes` 都必须至少包含一个条目。
- 每个类别必须有且只有一个默认安装路径。

### 6.4 software_overrides

必须为数组，可为空。每个特例对象必须包含：

- `software_id`
- `display_names`
- `aliases`
- `priority`
- `category`
- `install_path`
- `reason`

可选字段：

- `data_path`
- `cache_path`
- `installer_archive_path`

约束：

- `software_id` 必须全局唯一。
- `display_names` 至少包含一个正式名称。
- `priority` 必须高于类别默认规则优先级。
- `category` 必须引用受控类别枚举。
- `install_path` 必须属于该类别允许路径集合，或被额外声明为特例允许路径。
- `data_path`、`cache_path` 仅表示本地目录，不得表示同步目录。

### 6.5 conflict_resolution

必须显式声明规则命中顺序。推荐固定为：

1. 软件精确名称命中
2. 软件别名命中
3. 软件特例关键词命中
4. 类别关键词命中
5. 类别默认规则
6. 全局硬规则
7. 默认回退

不得把冲突顺序藏在说明文字中。

### 6.6 validation_examples

必须提供最少 10 个样例软件，作为文档级验收样本。

每个样例至少包含：

- `software_name`
- `expected_category`
- `expected_install_path`
- `expected_rule_source`

## 7. 字段语义要求

### 7.1 必须保留的路径字段

- `install_path`
- `data_path`
- `cache_path`
- `installer_archive_path`

### 7.2 明确禁止的字段

- `sync_path`
- `cloud_path`
- `onedrive_path`
- `remote_backup_path`
- `vault_sync_path`

### 7.3 路径约束

- 所有路径必须为 Windows 绝对路径。
- 统一使用反斜杠 `\`。
- 目录路径不得带尾部说明文字。
- 同一字段不得混入多个候选路径。

## 8. 文本编写要求

下一版规则文档禁止使用以下写法作为机器规则：

- “通常”
- “一般”
- “尽量”
- “建议可以”
- “视情况而定”
- “也可以放到”
- “若觉得合适”

允许出现这类文字的唯一位置是“面向人类的备注区”，且该备注区不得被解析器消费。

## 9. 类别设计要求

每个类别必须满足“定义可互斥”原则。为避免模型误判，每个类别必须同时声明：

- 该类别是什么
- 典型包含哪些软件
- 明确排除哪些软件

示例原则：

- `media_design` 表示创作、编辑、处理图像/音频/视频的软件。
- `games_entertain` 表示游戏平台、音乐客户端、娱乐平台等消费型客户端。
- `productivity` 表示文档、表格、脑图、笔记、PDF 等办公效率软件。

对于跨界软件，不允许只写“音频软件”或“笔记软件”这种宽泛定义，必须明确是“创作工具”还是“消费客户端”。

## 10. 特例规则要求

以下类型的软件应优先写入 `software_overrides`，而非只依赖类别默认规则：

- 多义性强的软件
- 软件名容易误导类别的软件
- 安装路径和数据路径分离的软件
- 与通用类别默认路径不完全一致的软件
- 中文名、英文名、简称混用的软件

特例规则示例场景：

- `Obsidian`
- `网易云音乐`
- `QQ 音乐`
- `Steam`
- `OBS Studio`

## 11. 验收硬指标

设计完成后，规则文档必须满足以下硬性指标：

1. 不读取备注区，仅靠结构化规则块即可完成软件分类与安装路径决策。
2. 对验收样例中的每个软件，分类结果唯一。
3. 文档中任一软件未写入特例时，不得同时命中两个类别且无法裁决。
4. 任一类别默认路径都必须位于 `D:\`。
5. 任一全局禁止安装根路径都不得位于 `D:\`。
6. 文档不得包含云同步字段或 OneDrive 路径。
7. 新增单个软件特例时，不需要修改解析器的类别推断代码。
8. 任一特例删除后，受影响的软件范围可以通过 `software_id` 追踪。
9. 程序解析失败时，能定位到具体字段，而不是只报“规则格式错误”。
10. 文档在 UTF-8 编码下可稳定读取。

## 12. 推荐文档骨架

````md
# Smart Filer Machine Rules

```yaml
metadata:
  rules_version: 1
  document_type: smart_filer_machine_rules
  document_status: draft
  platform: windows
  path_style: windows_absolute

global_rules:
  preferred_install_drive: "D:"
  forbidden_install_roots:
    - "S:\\"
  fallback_install_path: "D:\\10_Environments"
  allow_only_local_paths: true

categories:
  - id: productivity
    display_name: Productivity
    priority: 400
    definition: "General office and knowledge-work software."
    includes:
      - "Office"
      - "Notion"
      - "Obsidian"
    excludes:
      - "music client"
      - "video editor"
    default_install_path: "D:\\40_Productivity"
    allowed_install_paths:
      - "D:\\40_Productivity"

software_overrides:
  - software_id: netease_cloud_music
    display_names:
      - "网易云音乐"
      - "NetEase Cloud Music"
    aliases:
      - "网易云"
      - "云音乐"
    priority: 1000
    category: games_entertain
    install_path: "D:\\70_Games_Entertain"
    data_path: "D:\\20_Communication_Data\\NetEaseCloudMusic"
    reason: "Music client belongs to entertainment client group."

conflict_resolution:
  order:
    - exact_name
    - alias
    - override_keyword
    - category_keyword
    - category_default
    - global_hard_rule
    - fallback

validation_examples:
  - software_name: "OBS Studio"
    expected_category: media_design
    expected_install_path: "D:\\50_Media_Design"
    expected_rule_source: category_default
```
````

## 13. 实施建议

建议实施顺序如下：

1. 先产出新的机器优先规则文档规范。
2. 再基于该规范重写 `文件结构.md` 或拆分为“人类版 + 机器版”双文档。
3. 随后重写 `document_parser.py`，从关键词猜测转向结构化字段读取。
4. 最后补齐文档解析与冲突场景测试。

## 14. 当前结论

- 当前自然语言版 `文件结构.md` 仍可继续服务现有实现。
- 下一版规则系统必须引入机器优先结构化规范。
- 新规范中不包含云同步概念。
- 后续如需云同步，应另行设计专门文档，而不是重新混入规则主文档。
