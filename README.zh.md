# 矩墨RulesInk（中文版）

[English Version](README.md)

> 一个具备 L1–L2–L3 分层治理、自进化闭环和宪法约束层的自主 AI 组织。
> MIT 协议。

## 项目介绍

矩墨RulesInk（HNO）是一套自主治理 AI Agent 架构的开源参考实现。核心特性：

- **L1–L2–L3 治理层级** — CEO → 域总经理 → 执行助理
- **域内自进化闭环** — 每个域自动检测并修复自身能力缺口
- **SOUL.md 约束层** — 宪法级约束，防止越权
- **dispatch_guard 插件** — Hermes Agent 的 pre_tool_call 门禁执行（CLI + Agent 双层）
- **门禁提案机制** — L1 执行 terminal/execute_code 前必须向用户提案
- **Enterprise Advisory Council** — 多角度并发专家分析（顾问，无决策权）
- **Company Capability Development Protocol** — 标准化能力贡献流程

## 版本更迭 / Version History

> 矩墨RulesInk 采用"先治理，后扩展"的架构演进策略。每个大版本对应宪法约束层的一次成熟里程碑。

| 版本 | 日期 | 里程碑 | 仓库 |
|------|------|--------|------|
| v1.0 | 2026-05-11 | 初始版本：L1–L2–L3 治理层级 + SOUL.md 接口规格 + 6域自进化闭环 | [hermes-native-organization-legacy](https://github.com/Leedhao1029/hermes-native-organization-legacy) |
| v3.5.0 | 2026-05-26 | 门禁系统完整落地：dispatch_guard 插件 + 门禁提案机制 + Soul Arbiter 宪法仲裁（9个接入点） + coordination_protocol v2.2 | [rulesink](https://github.com/Leedhao1029/rulesink) |

**演进逻辑：**
- v1.0 → v3.5 不是"功能增加"而是"治理成熟"
- 约束层（SOUL.md）从接口规格演化为生产级仲裁引擎
- 门禁系统（dispatch_guard）专为堵住 L1 越级 L2→L3 编排链路的架构缺口而建
- 所有历史提交完整保留于归档仓库，作为演进过程的见证

## 项目哲学 / Project Philosophy

> 我们坚信，AI 组织的治理不应建立在"自觉"之上，而应建立在硬性的、代码级的宪法约束之上。因此，我们的首要任务是将 SOUL.md 宪法和其 SOUL Arbiter（审计与执法引擎）打磨到生产级，而不是急于开源一个功能繁多但治理薄弱的原型。
>
> 本项目采用"先治理，后扩展"的架构演进策略。我们选择一条更困难但更负责任的道路——先确保核心治理层（L1-L3架构、SOUL Arbiter、自进化引擎、长链路任务管理）的可靠与可审计，再逐步扩展对外的功能模块。

---

>We believe that the governance of AI organizations should not be built on 'compliance promises' but on hard-coded, constitutional-level constraints. Therefore, our immediate priority is to refine the SOUL.md constitution and its SOUL Arbiter (audit & enforcement engine) to production-grade, rather than rushing to open-source a feature-rich but weakly-governed prototype.
>
>This project follows a 'Governance First, Features Later' architectural evolution strategy. We are taking a harder but more responsible path — ensuring the core governance layer (L1-L3 hierarchy, SOUL Arbiter, self-evolution engine, long-task context manager) is reliable and auditable before progressively expanding the functional modules.

## 架构总览

```
L1 CEO
  ├── 门禁执行系统（dispatch_guard 插件 + Soul Arbiter）
  └── L2 域编排器（IT / 电商 / 建筑 / 投资 / 生活 / 多模态）
        └── L3 技能代理（每个域 180+ 脚本）
```

详细架构文档见 [ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 快速开始

```bash
pip install -e .
python3 -c "from hermes_native_organization import dispatch; print(dispatch('帮我分析一下电商转化率'))"
```

## 开源与闭源边界

我们开源 **架构、接口和工作流**。
我们保留专有 **具体阈值、模式数据库和学习算法**。

### 开源部分（MIT）

| 组件 | 开放内容 |
|------|---------|
| `dispatcher.py` | L1 意图路由接口 — 完整7域关键词系统已移除 |
| `it_orchestrator.py` | IT L2 编排循环 — 阈值和路由表已移除 |
| `advisory_council.py` | 4顾问面板 — 分析逻辑专有 |
| `l3_base.py` | L3 基类 — 完整实现（350行） |
| `soul_arbiter.py` | SOUL 约束接口 — 模式引擎已移除 |
| 自进化模块 | 5阶段闭环架构 — 触发阈值专有 |
| CCDSP 协议 | 7章治理框架 — 完整实现 |

### 专有部分（不在本仓库）

- 关键词→域评分权重
- 熔断轮次限制和预算上限
- 自传体学习算法
- SOUL 模式匹配器和阈值
- 顾问分析提示词模板
- 锻造队列触发阈值

## 企业专家顾问团

本版本新增模块。顾问团是 **临时性、仅咨询性质的专家小组**：

```
问题 ──▶ [战略顾问] ──┐
      ──▶ [技术顾问] ──┼──▶ 综合报告 ──▶ CEO
      ──▶ [风险顾问] ──┤
      ──▶ [进化顾问] ──┘
```

**治理规则：**
- 仅咨询性质 — 不替代 L2 决策权
- IT 部门拥有并审计所有输出
- 不直接执行 L3 脚本
- 从已批准决策中提取模式 → 自动注册为 Skill

## 治理实证 / Governance Evidence

> SOUL Arbiter 是宪法约束层的实际执行器，在每一次路由决策中被动触发并写入审计日志。以下为生产环境实测记录。

### 核心证据：生产事件审计日志

```
会话: construction_task_session
时间戳 (UTC)        类别                  动作                    域             结果  触发原因
─────────────────────────────────────────────────────────────────────────────────────────────
2026-05-11T08:06:34 意图识别审计          intent_routed          construction  PASS  用户输入触发领域识别，命中 construction（置信度 0.79）
2026-05-11T08:06:34 调度越权拦截          cross_domain_resolved  construction  PASS  跨域协调
2026-05-11T08:06:34 授权矩阵判断          authorize              construction  PASS  域 'construction' 授权执行编排器
2026-05-11T08:06:50 意图识别审计          orchestrator_executed  construction  PASS  编排器执行完成，返回码 0
2026-05-11T08:06:50 意图识别审计          orchestrator_executed  construction  FAIL  编排器执行完成，返回码 1
2026-05-11T08:06:50 调度越权拦截          l3_mismatch_check      construction  PASS  L3 能力验证通过，未触发补建
2026-05-11T08:06:50 授权矩阵判断          authorize              it            PASS  域 'it' 授权执行编排器
```

**总计：7 条 soul_arbiter 事件，写入 events.jsonl（总计 4,230 条生产事件）**

### SOUL Arbiter 接入点说明

| 接入点 | 位置 | 触发时机 | 事件类型 |
|--------|------|---------|---------|
| 意图识别审计 | `classify_intent()` 之后 | 每个任务入口 | `intent_routed` |
| 跨域协调审计 | `coordinate()` 之后 | 跨域任务 | `cross_domain_resolved` / `BLOCK` |
| 编排器授权检查 | `run_orchestrator()` 入口 | 每个编排器调用前 | `authorize` / `BLOCK` |
| L3 缺失检测 | `_auto_trigger_it()` 返回后 | 补建触发判断 | `l3_mismatch_check` / `FLAG` |
| 熔断触发审计 | `retry_depth >= 3` 时 | 重试超限 | `circuit_open` → `CIRCUIT_OPEN` |
| 编排器结果审计 | `run_orchestrator()` 返回时 | 成功/异常 | `orchestrator_executed` |

### 查询命令

```bash
hermes --soul-stats           # 近24小时 SOUL Arbiter 统计
hermes --soul-stats 168       # 近7天统计
hermes --events               # 查看全部事件日志（包含 soul_arbiter 事件）
```

### 真实案例：执行层审计盲区发现与修复（2026-05-11）

> 以下为生产数据驱动的精准修复过程，是系统"自我审计能力"的直接证据。

**问题发现**：`life-health` 累计 146 次直接调用，0 次经过任何质量门禁。IT 域 1,472 次 skill 调用，soul_arbiter 仅 1 条（盲区率 99.93%）。

**根因**：SOUL Arbiter 仅覆盖"编排层"（6个接入点），未覆盖"执行层"（`skill_invoke` 链路）。

**修复**：
- 接入点7：`audit_skill_invoke()` 新增健康类 skill 识别
- 接入点8：`audit_health_skill_content()` 健康类 skill 内容审计（94个医疗越权关键词）
- 接入点9：编排器返回前对 life 域做二次复核
- L2标签统一：audit 日志 domain 字段全部中文化

**验证**：`audit_health_skill_content()` 实测输出：
```
result=BLOCK, action=medical_overreach_direct
  skill=life-health
  medical_overreach_keywords: ['CA125', '卵巢癌']
  via_orchestrator: False
```

**完整案例报告**：[`docs/DIAGNOSIS.md`](docs/DIAGNOSIS.md)

### 透明可审计原则

所有 SOUL Arbiter 事件包含：
- **触发原因** (`trigger_reason`)：为什么触发
- **涉及层级** (`involved_l1_parts`)：哪些 L1 组件参与决策
- **拦截结果** (`result`)：`PASS` = 正常通行 / `FLAG` = 能力缺口 / `BLOCK` = 越权拦截 / `CIRCUIT_OPEN` = 熔断
- **完整上下文** (`extra`)：原始任务、返回码、错误信息

## 项目结构

```
ju-mo-rulesink/
├── hermes/                          # 核心框架
│   ├── __init__.py
│   ├── dispatcher.py                 # L1 意图路由（1735行 → 公共接口）
│   ├── l3_base.py                   # L3 基类（350行 — 完整）
│   └── soul_arbiter.py              # SOUL 约束接口
├── domains/                         # 域自进化闭环
│   ├── it/
│   │   ├── orchestrator.py           # 4094行 → 公共架构
│   │   └── self_evolution.py         # 802行 → 公共接口
│   ├── ecommerce/self_evolution.py   # 730行 → 公共接口
│   ├── construction/self_evolution.py
│   ├── investment/self_evolution.py  # 841行 → 公共接口
│   ├── life/self_evolution.py
│   └── multimodal/self_evolution.py
├── council/
│   └── advisory_council.py           # 1033行 → 公共架构
├── dispatch_guard/                    # 门禁执行插件（CLI + Agent 双层）
├── skills/
│   ├── enterprise-advisory-council/SKILL.md
│   └── company-capability-development-protocol/SKILL.md
├── protocol/
│   └── company_capability_development_protocol.py
└── examples/
    ├── minimal_demo.py
    └── advisory_council_example.py
```

## 自进化闭环

每个域实现5阶段闭环：

```
ANALYZE → DIAGNOSE → PLAN → EXECUTE → LEARN
   ↑                                     │
   └─────────────────────────────────────┘
```

| 阶段 | 行为 |
|------|------|
| ANALYZE | 扫描 L3 脚本、skills、归档 |
| DIAGNOSE | 分类问题：MISSING_SKILL / WEAK_SKILL / BROKEN_SCRIPT |
| PLAN | 生成构建提案 |
| EXECUTE | 仅在用户确认后执行变更 |
| LEARN | 记录到自传体用于路由改进 |

## CCDSP — 公司能力开发标准协议

7章治理框架（完整文档见 `protocol/`）：

```
第一章: 总则          — 五项核心原则
第二章: 自主进化权     — 各 L2 自主拥有进化模块
第三章: 贡献规范      — 6步贡献工作流
第四章: 共享归属      — 共享能力属于公司
第五章: 跨部门协作     — 主责+配合域规则
第六章: 技术中台      — IT 是平台而非服务商
第七章: 附则          — 执行与修订
```

## 文档

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — 完整架构参考
- [GETTING_STARTED.md](docs/GETTING_STARTED.md) — 安装与首次使用
- [CONTRIBUTING.md](docs/CONTRIBUTING.md) — 贡献指南

## 协议

MIT — 见 [LICENSE](LICENSE)。

## 联系方式

| 渠道 | 账号 |
|------|------|
| Email | lidonghao1029@me.com |
| 电话 | +86 15361474556 |
| 微信 | LeedHao |
| 个人主页 | [leedhao.top](http://leedhao.top/) |

## GitHub Pages

文档站点：https://leedhao1029.github.io/rulesink/
