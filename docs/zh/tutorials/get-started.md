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

## 第四步：试用与管理员应用

普通用户：

```text
/sharelife_trial community/basic
/sharelife_trial_status community/basic
```

状态会返回 `not_started`、`active` 或 `expired`，并带 TTL 信息。  
同一模板重复试用会进入管理员队列。

管理员队列处理：

```text
/sharelife_retry_list
/sharelife_retry_lock <request_id>
/sharelife_retry_decide <request_id> approve <request_version> <lock_version>
```

管理员应用流程：

```text
/sharelife_dryrun community/basic 1.0.0
/sharelife_apply <plan_id>
/sharelife_rollback <plan_id>
```

未传 `plan_id` 时会自动推导，如 `plan-community-basic`。

## 第五步：社区投稿与安装

普通用户投稿：

```text
/sharelife_submit community/basic 1.0.0
```

管理员审核：

```text
/sharelife_submission_list
/sharelife_submission_decide <submission_id> approve
```

用户安装路径：

```text
/sharelife_market
/sharelife_install community/basic
/sharelife_prompt community/basic
/sharelife_package community/basic
```

管理员审计：

```text
/sharelife_audit 20
```
