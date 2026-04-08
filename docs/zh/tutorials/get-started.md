# 快速开始

本教程给出 `sharelife` 在本地可落地的最小流程，步骤尽量保持最短。

## 快速路径

```bash
bash scripts/sharelife-init-wizard --yes --output config.generated.yaml
```

然后在聊天里执行：

```text
/sharelife_pref
/sharelife_market
/sharelife_trial community/basic
/sharelife_trial_status community/basic
```

能跑通后再继续下面步骤。  
一屏版可看 [3 分钟快速跑通](/zh/tutorials/3-minute-quickstart)。

## 前置条件

1. Python 3.12
2. AstrBot 运行环境
3. 已执行 `pip install -r requirements.txt`

可选：执行 `/sharelife_webui` 打开独立 WebUI。

## 第一步：检查默认偏好

```text
/sharelife_pref
```

默认应包含：

- `execution_mode=subagent_driven`
- `observe_task_details=off`

## 第二步：切换执行模式

```text
/sharelife_mode inline_execution
```

再次执行 `/sharelife_pref`，确认已切换。

## 第三步：开启任务细节观测

```text
/sharelife_observe on
```

再次执行 `/sharelife_pref`，确认 `observe_task_details=on`。

## 第四步：试用与本地安装交接

普通用户：

```text
/sharelife_trial community/basic
/sharelife_trial_status community/basic
```

状态会返回 `not_started`、`active` 或 `expired`，并带 TTL 信息。

随后继续本地用户安装链路：

```text
/sharelife_market
/sharelife_prompt community/basic
/sharelife_package community/basic
```

真正的安装控制在本地 WebUI 的 `/member` 或 `/market` 中完成，可选项包括：

- `preflight`
- `force_reinstall`
- `source_preference=auto|uploaded_submission|generated`

## 第五步：上传与社区投稿

模板上传链路：

1. 打开本地 WebUI 的 `/member` 或 `/market`。
2. 选择模板包文件，或使用已生成的 package 输出。
3. 模板包直传上限为 `20 MiB`。
4. 可选上传参数：
   - `scan_mode=strict|balanced`
   - `visibility=community|private`
   - `replace_existing=true|false`
5. 提交后通过 `我的投稿` 查看结果。

Profile-pack 投稿链路：

1. 准备或导出本地产物，复制其 `artifact_id`。
2. 在 `/member` 或 `/market` 发起投稿。
3. 可选提交参数：
   - `pack_type`
   - `selected_sections`
   - `redaction_mode`
   - `replace_existing`
4. 通过 `我的 Profile-Pack 投稿` 查看属主范围内的状态与导出下载。
