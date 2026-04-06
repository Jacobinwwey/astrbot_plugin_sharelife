# 初始化向导与配置模板

本页把“读文档配置”改成“执行命令直接拿到可用配置”。

## 目的

1. 降低首次安装时的配置偏差。
2. 缩短从安装到跑通的时间。
3. 让配置说明和配置文件保持同源。

## 运行向导

交互模式：

```bash
bash scripts/sharelife-init-wizard --output config.generated.yaml
```

默认值模式：

```bash
bash scripts/sharelife-init-wizard --yes --output config.generated.yaml
```

常用参数：

1. `--provider openai|claude|deepseek`
2. `--api-key <value>`
3. `--preset standard_qa|sharelife_companion|research_safe`
4. `--webui-auth true|false`
5. `--allow-anonymous-member true|false`
6. `--anonymous-member-user-id <value>`
7. `--anonymous-member-allowlist "POST /api/trial,GET /api/trial/status,..."`
8. `--enable-plugin-install-exec true|false`
9. `--print-only`

## 配置模板

`config.template.yaml` 是基准模板，建议长期留在仓库。

模板覆盖：

1. provider 和模型配置。
2. WebUI 鉴权与登录限流。
3. profile-pack 的签名和加密字段。
4. 插件安装执行门禁（默认关闭、前缀白名单、超时限制）。
5. 匿名 member 模式默认值与端点白名单覆盖字段。

## 推荐团队流程

1. 仓库只提交 `config.template.yaml`。
2. 本地通过向导生成 `config.generated.yaml`。
3. 密钥只放私有文件，不入 git。
4. 每次改配置后，用 `/sharelife_pref` 与 `/sharelife_trial_status` 做冒烟验证。
