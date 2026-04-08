# 3 分钟快速跑通

目标：先快速验证用户侧链路可用，再进入本地 WebUI 的完整操作流。

## 0. 人类快速安装（最简）

```bash
pip install -r requirements.txt
bash scripts/sharelife-init-wizard --yes --output config.generated.yaml
pytest -q && node --test tests/webui/*.js
```

需要交互式输入时：

```bash
bash scripts/sharelife-init-wizard --output config.generated.yaml
```

## 1. 面向 AI 的一键安装 Prompt（复制即用）

```text
你是终端安装代理，当前目录是 `astrbot_plugin_sharelife`。严格执行：(1) `pip install -r requirements.txt`；(2) `bash scripts/sharelife-init-wizard --yes --output config.generated.yaml`；(3) `pytest -q`；(4) `node --test tests/webui/*.js`。任一步失败就停止，仅输出：失败步骤 + 根因 + 精确修复命令。全部成功仅输出：`READY`、配置文件路径、以及 4 条验证命令：`/sharelife_pref`、`/sharelife_market`、`/sharelife_trial community/basic`、`/sharelife_trial_status community/basic`。
```

## 2. 在聊天里验证

```text
/sharelife_pref
/sharelife_market
/sharelife_trial community/basic
/sharelife_trial_status community/basic
```

预期结果：能看到明确 trial 状态，市场命令返回可用数据。

## 3. 验证用户侧交接

1. 通过 `/sharelife_webui` 打开本地 WebUI。
2. 在 `/member` 或 `/market` 中执行受保护的用户动作。
3. 继续完成安装、上传或 profile-pack 投稿。
4. 高权限审核与恢复流程不在公开文档中展开。

## 4. 后续阅读

1. [快速开始](/zh/tutorials/get-started)
2. [初始化向导与配置模板](/zh/how-to/init-wizard-and-config-template)
3. [QUICKSTART.md](https://github.com/Jacobinwwey/astrbot_plugin_sharelife/blob/main/QUICKSTART.md)
