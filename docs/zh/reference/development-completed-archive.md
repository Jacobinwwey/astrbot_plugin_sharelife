# 开发完成归档（公开）

> 最近更新：`2026-04-11`  
> 范围：已完成且可在代码/测试/文档中公开验证的事项

## 已完成主线

1. 权限边界基线
- member/reviewer/admin/market 已实现页面与路由边界分离，鉴权语义固定为 `401` / `403`。
- member 模板已从源头移除特权控件，不再依赖 CSS 隐藏。

2. 公开发布安全门禁
- public promotion gate 已阻断私有文档根、secret 类本地文件、gitlink/submodule 模式变更、allowlist 外新增路径。
- private->public 同步已纳入 projection manifest 与测试约束。

3. 市场与用户能力门控收敛
- 市场能力门控运行时已复用共享 helper，降低页面间授权漂移。
- 匿名 member allowlist 已覆盖 API 与 WebUI 合约测试。

4. 持久化执行与安装契约
- 上传/安装/提交流程选项契约已统一。
- 提交流程已落地幂等冲突拒绝（`idempotency_key_conflict`）。

5. 分解治理门禁
- 已对关键单体文件引入 CI 行数预算，防止重构过程中再次耦合膨胀。

## 验证来源

1. `tests/infrastructure/test_public_promotion_gate.py`
2. `tests/meta/test_market_capability_runtime_surface.py`
3. `tests/meta/test_decomposition_budget_surface.py`
4. `tests/interfaces/test_webui_server.py`
5. `tests/meta/test_permission_boundary_roadmap_surface.py`

## 边界说明

本页仅维护公开接口与行为契约归档。  
运维 SOP、secret 轮换、特权恢复流程继续保留在私有文档。

