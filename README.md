# Taskbook

![Taskbook 图标](logo.ico)

一个基于 PySide6 的桌面任务管理与日报生成工具，内置单实例守护、托盘支持、任务筛选导出/导入，以及 AI 日报生成。

## 功能特性
- **任务管理**：新增、编辑、批量完成、批量删除，多选操作。
- **筛选与搜索**：关键词、状态筛选，截止时间快捷筛选（今天/本周/本月），自动搜索防抖。
- **截止时间必填**：新建任务默认设置当日 18:00，过 18:00 自动顺延次日。
- **导出/导入 Excel**：
  - 导出当前筛选结果或选中任务为 `.xlsx`（不含 ID，状态使用中文）。
  - 导入任务：标题、状态、优先级、截止日期、更新时间、描述均为必填。
  - 内置导入示例模板，可在界面一键保存。
- **提醒**：
  - 到期提醒小弹窗；可设置提醒开关、阈值。
  - 定期提醒待办/进行中任务，用户可设定间隔分钟。
  - 每日首次启动弹出作者信息框。
- **主题**：亮/暗/透明三种主题，透明度可调。
- **单实例 + 托盘**：全局只运行一个实例；最小化到托盘后再次启动会唤回已有窗口。
- **日报生成**：选中任务后生成日报，等待弹窗防重复点击；富文本预览可复制。

## 运行环境
- Python 3.10+
- Windows 10/11（托盘和本地通知基于 Windows 环境）

## 安装依赖
```bash
pip install -r requirements.txt
```

## 开发运行
```bash
python run.py
```
启动后会自动初始化 SQLite 数据库 `data/taskbook.db` 并写入默认日报模板。

## 打包
使用 PyInstaller onefile 打包，记得把 `schema.sql` 一并打入：
```bash
python -m PyInstaller \
  --onefile --windowed --icon image.png \
  --add-data "app/db/schema.sql;app/db" \
  run.py
```
产物在 `dist/` 目录。

如需 Inno Setup 安装包，可参考仓库中的 `Taskbook.iss`，图标使用 `image.png`。

## 目录结构
```
app/
  db/               # SQLite 初始化
  models/           # 数据模型
  repositories/     # 数据访问与设置
  services/         # 业务服务（日报、提醒等）
  ui/               # PySide6 界面
run.py              # 入口
requirements.txt
schema.sql          # DB 初始化（随 app/db/schema.sql 打包）
```

## 导入 Excel 模板
- 表头：`标题, 状态, 优先级, 截止日期, 更新时间, 描述`
- 状态取值：`待办 / 进行中 / 已完成`
- 优先级：1/2/3
- 日期时间格式：`YYYY-MM-DD HH:MM:SS`
- 应用内可点击“保存导入示例”生成 `task_import_sample.xlsx`。

## 配置与安全
- AI 接口使用 OpenAI 兼容 Chat Completions，要求 HTTPS。
- API Key 建议通过系统凭据存储（keyring），避免明文落盘。
- 模型与 Prompt 配置在本地 SQLite 中保存，默认提供日报模板。

## 已知限制
- 仅测试于 Windows 环境。
- AI 生成依赖外部接口，请确保可联网且配置正确。

## 许可证
MIT License
