# 开发进行中推进清单（公开）

> 最近更新：`2026-04-11`  
> 范围：当前仍在推进的公开功能线

## 主线 A：用户上传链路收口

状态：`进行中`

已完成：

1. 上传细则弹层与市场细则页交互一致性收口。
2. 本机 AstrBot 导入后 section 深层内容可视化选择（支持更深嵌套节点）。
3. 上传细则按草稿记忆审阅状态（弹层重开 + 同会话刷新可恢复）。
4. 本机 AstrBot 重扫去重已改为“按最新草稿确定性折叠”，即使导入存储顺序漂移也不会误显示旧草稿。

待推进：

1. 继续收敛长链路导入/投稿/撤回的 E2E 稳定性。

公开验收标准：

1. 用户可稳定完成导入 -> 审阅 -> 投稿 -> 撤回闭环。
2. 上传细则支持更细粒度 section 选择并可见生效差异，且当前浏览器会话内状态恢复确定。

## 主线 B：AstrBot 互通稳健性

状态：`进行中`

已完成：

1. 导入诊断已输出确定性的问题分组桶（`integrity`、`security`、`version`、`conversion`、`environment`、`unknown`），并在导入载荷与审阅证据中保持一致。
2. 导入诊断已输出字段级 issue 详情（`sections`、`related_paths`、`evidence_refs`），支持无需手工翻 payload 的路径级分诊。
3. 用户侧兼容性指导已接入 `compatibility_issue_details`，前端动作可保留 issue 级 section/path/evidence 元数据。
4. 原始 AstrBot 转换已输出字段级转换诊断（`summary.field_diagnostics`），当扫描证据缺失时可用这些诊断回填 conversion issue 的 `evidence_refs`。

待推进：

1. 持续完善原始 AstrBot 导出包与 profile-pack 规范模型的映射。
2. 提升“字段级”不兼容诊断可读性与降级提示。

公开验收标准：

1. 导入结果始终输出确定性的 `compatibility_issues`。
2. 已声明支持的 section 不出现静默丢失。

## 主线 C：文档与公开面治理

状态：`进行中`

1. 公开文档只保留接口与行为契约，私有流程留在 private docs。
2. 新增文档保持三语结构一致与导航可达。

公开验收标准：

1. i18n 结构与 docs 构建校验持续通过。
2. 公共提交在 promotion gate 下保持 PASS。

## 主线 D：CI 与 E2E 稳定化

状态：`进行中`

1. 继续定位并收敛 WebUI E2E 波动点。
2. 保持跨环境测试数据的确定性。

公开验收标准：

1. main 分支 `ci` 多次提交稳定通过。
2. E2E 失败具备根因标签与跟踪状态。
