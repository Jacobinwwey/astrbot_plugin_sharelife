# 2026-04-06 v2.1 - Sharelife 市场细则层 Stitch 设计说明

## 元信息

- 日期：2026-04-06
- 版本：v2.1
- 状态：已确认当前 Stitch 基线，五个变体已发起生成请求
- 说明：本文件是中文说明稿，真正用于 Stitch 调用的 canonical prompt source 是 `Design.md`

## 目标界面与用户任务

目标界面是从 `/market` 卡片打开后的细则层。

用户任务是：

1. 理解当前选中的 pack 是什么
2. 查看公开事实与风险信号
3. 选择试用、安装、对比或下载等成员动作
4. 在不离开当前 pack 上下文的前提下调整安装同步范围

## 当前市场中心基线

细则层必须从当前已经实现的 `/market` 基线派生，而不是从任何旧的 market-hub 设计派生。

当前基线包括：

1. public-first 的市场入口
2. 紧凑、单色、偏 editorial-technical 的头部
3. 位于头部下方的大型 Spotlight 式搜索框
4. 位于搜索框下方的克制排序与结果控制行
5. filter rail + public card grid 的浏览界面
6. 仅在点击卡片后打开的 detail shell

细则层必须看起来像这一基线自然展开的下一层，而不是独立产品页或重新发明的 dashboard。

## 必须遵守的数据 Contract

细则层必须继续使用稳定 contract：

1. `pack_id`
2. display title
3. `version`
4. `maintainer`
5. `pack_type`
6. `risk_level`
7. `compatibility`
8. `review_labels`
9. `warning_flags`
10. `sections`
11. 摘要或描述
12. 更新时间
13. 公开 source / audit 事实

## DOM 与运行时约束

生成结果不能破坏：

1. `marketDetailArea`
2. `marketDetailControlStore`
3. `marketDetailActionCluster`
4. `marketDetailInstallSectionsShell`
5. `marketDetailInstallOptionsShell`
6. `marketSummary`

还必须保留：

1. 桌面抽屉 / 移动端 sheet 行为
2. 切换变体时保持 pack 上下文
3. 只有真正触发成员动作时才鉴权
4. 与 standalone script + globalScope 导出模型兼容

## 细则层派生规则

必须强继承当前市场中心基线：

1. 延续当前单色技术编辑感
2. 继续坚持 public facts 优先、actions 次之
3. 继续保持“页面负责 browse，细则层负责 act”
4. 继续保持克制，不做剧烈风格跳变
5. 让 action rail 看起来是当前页面的一部分
6. 正式发布的动作控件要并入主细则面板，不能再在下方保留第二张“成员操作”卡片

允许变化：

1. 细则层内部信息重排
2. trust / facts / actions 的顺序调整
3. evidence 与 metadata 的分组调整

不允许：

1. 偏离当前市场中心的人格与视觉基调
2. 引入另一套完全不同的视觉系统
3. 让细则层比来源页面更像主界面
4. 回退使用旧 Stitch market-hub 方案作为视觉来源

## Stitch 调用基准

真正调用 Stitch 时，使用 `Design.md` 中的英文 prompt block 作为唯一调用来源，不要把中文与日文混入同一 prompt source。

固定产品规则：

1. Stitch 只接管 clicked-card detail layer，不重做 market 首屏
2. 内部仍保留五个设计 variant 作为对照输入，但正式细则层不再展示“方案 1-5”切换行
3. 必须保留清晰的 member action rail
4. 公开事实在登录前可阅读
5. 只有成员动作真正开始时才鉴权
6. install 前必须支持按 section 选择同步范围
7. `memory_store`、`conversation_history`、`knowledge_base` 这类 stateful / local-data section 必须表现为可选同步对象
8. 上传与提交相关流程归属用户面板，不再放进细则层

## 当前本地实现推进方向

当前本地推进方向已锚定在 `variant_3`：

1. `variant_3` 是第一优先深化对象
2. 左侧放公开事实，右侧放成员动作就绪信息
3. 真实受保护动作直接并入 `操作就绪` 区块，而不是放在 viewport 下方的独立卡片
4. 安装时 section-selective sync 属于 native member-action flow
5. `memory_store`、`conversation_history`、`knowledge_base` 可以在安装时主动取消选择
6. install-sync section 是细则层内唯一保留的 section 视图，不再重复放置“已声明 Sections”
7. 安装来源 / 仅预检 / 强制重装以及本地安装状态与列表要放在安装同步项与审阅信号之间
8. 上传与提交 UI 不再出现在细则层
9. 后续如果再次调用 Stitch，必须先更新 `Design.md`

## 验收检查

1. 切换 variant 时 pack context 保持稳定
2. member action rail 仍然可用
3. 任一 variant 不得丢失必需公开事实
4. 任一 variant 不得破坏 standalone WebUI 运行时模型
5. 新结果必须明显继承当前市场中心基线
6. 如重新向旧 market hub 漂移，直接判为不合格

## 当前有效结果

- 旧 session `14909211256281812924` 与后续归档项目 `projects/614617403044256572` 仅保留作历史对照，不再作为当前视觉基线。
- 当前已确认成功的基线项目：`projects/1791941634823407461`
- 当前已确认成功的基线 screen：`3ef1d2a12c3449f593141520a70ec987`
- 基线标题：`Sharelife Market Detail Concept`
- 当前五变体状态：
  - variant session：`14727920063696137864`
  - `variant_1`：`0a22321fc4244a8cbb4b80c7ff88543a`
  - `variant_2`：`926623465dd94241a9f2f4ba68811dad`
  - `variant_3`：`4d71151e5e0a499fbbb9e2b78b7676aa`
  - `variant_4`：`2faed839bb5d4de4ad6887c795b30733`
  - `variant_5`：`9ad760cf710c4b83972b04fbe2e39580`
- 当前实施偏好：
  - `variant_3` 继续作为原生实现主锚点
  - `variant_5` 作为执行清单导向的补充参考最清晰
  - `variant_2` 更适合作为高密度操作台参考，不宜直接作为默认主方向
