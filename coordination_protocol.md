# Coordination Protocol（协调协议）

**版本**：v2.2
**日期**：2026-05-15
**状态**：**生效**
**管辖权**：L1 CEO（小墨）
**宪法依据**：SOUL.md v3.2 不可变宪法

---

## 0. 宪法对齐声明

本协议严格遵循 SOUL.md v3.2 的以下不可变条款：

| SOUL.md 条款 | 本协议实现 |
|-------------|-----------|
| 核心原则：只做裁判，不做选手 | 跨域协调是 L1 职责，IT 仅是建造者+审计者 |
| 核心原则：数据流转不断层 | 配合方产出直接作为主责方输入参数（金字塔汇报） |
| 决策矩阵：L1跨部门冲突仲裁是最终裁决 | L1裁决权无条件，不受时效约束，是最终权力 |
| 永久机构：顾问团无决策权 | 顾问输出仅为 CEO 参考，不是签署/审批门禁 |
| 附录B：Soul Arbiter强制审计 | Soul Arbiter 是本协议的强制审计节点 |

---

## 1. 目的

Hermes系统当前存在跨域协调链路断裂问题：

- 各L2域接收用户任务后独立执行，无法协同处理涉及多域的复合任务
- 跨域任务缺少统一协调机制，主责域与配合域之间缺乏数据流转标准
- `coordinate()` 函数可输出结构化建议，但无触发配合域执行的链路

本协议授权 L1 重建跨域协调执行链路。IT 部门以"建造者+审计者"角色参与，不得以"协调者"身份驱动跨域任务。

---

## 2. 角色定义

### 2.1 L1 CEO（小墨）

| 职责 | 说明 |
|------|------|
| 跨域协调执行 | 跨域任务由 L1 直接驱动，不是委托 IT 驱动 |
| 主责/配合指定 | L1 决定哪个域为主责、哪些为配合 |
| 数据流转设计 | L1 设计配合方输出如何传递给主责方 |
| 最终裁决权 | **无条件的最终裁决权**，不受任何时效约束 |
| 金字塔汇报 | L1 接收跨域结果后，按金字塔格式汇报 |

### 2.2 IT部门

| 权限 | 说明 |
|------|------|
| 建造权 | 设计并实现 `coordination_executor.py` 的技术框架 |
| 标准化权 | 定义 data_flow 协议的**格式标准** |
| 审计权 | 对其他 L2 域的协调行为进行技术审计 |
| 建议权 | 向 L1 提供跨域任务分解建议，**但不强制 L1 采纳** |
| 汇报权 | 向 L1 汇报协调系统的运行状态 |

**IT 部门禁止**：
- 不得直接触发任何 L2 域执行
- 不得代替 L1 做跨域协调决策
- 不得以"协调者"身份自居

### 2.3 L2 域

| 职责 | 说明 |
|------|------|
| 参与权 | 按 L1 指定参与跨域任务（主责或配合） |
| 拒绝权 | 配合域可拒绝参与，但需向 L1 说明理由 |
| 自决策权 | 各域保留自身业务逻辑的独立决策权 |
| 汇报义务 | 配合域产出通过金字塔汇报格式传递给主责域 |

---

## 3. 协调流程（L1 执行链路）

### 3.1 步骤一：L1 感知与指定

```
用户任务
    ↓
L1 Perceive（复杂度评估）
    ↓
L1 指定：主责域 + 配合域 + 数据流转路径
    ↓
输出：《跨域协调执行令》
```

### 3.2 步骤二：L1 下发执行令

L1 向主责域和配合域下发结构化执行令：

```yaml
coordination_order:
  order_id: "<L1>-<时间戳>"
  issued_by: "L1_CEO"
  task: "<任务摘要>"
  primary: "<主责域>"
  supporting: ["<配合域>"]
  data_flow:
    inputs:
      <域>:
        - name: "<参数名>"
          type: "string/dict/list"
          required: true/false
          description: "<用途>"
    outputs:
      <域>:
        - name: "<输出名>"
          type: "<类型>"
          description: "<用途>"
  pyramid_report:
    # 金字塔汇报结构
    level_1_conclusion: "<一句话结论>"
    level_2_summary: "<3句话摘要>"
    level_3_detail: "<附录/原始数据>"
  escalation_deadline: null   # L1裁决无时效约束
```

### 3.3 步骤三：域执行与汇报

**配合域**：
- 接收执行令
- 执行配合任务
- 输出结构化结果（data_flow格式）
- 配合结果**直接传递**给主责域（数据流转不断层）

**主责域**：
- 接收配合域输出（直接作为输入参数）
- 执行主责任务
- 汇总所有输出，按金字塔格式输出最终汇报

### 3.4 步骤四：金字塔汇报 → L1

```
配合域输出
    ↓ 直接传递（不经IT中转）
主责域
    ↓ 金字塔汇报
L1 CEO
    ↓
金字塔格式输出：
  - Level 1：一句话结论
  - Level 2：三句话摘要
  - Level 3：附录/原始数据
```

---

## 4. IT 建造职责

### 4.1 coordination_executor.py 的定位

**不是协调者，而是技术基础设施建造者**。

coordination_executor.py 提供：
- 任务状态管理（pending/in_progress/completed/error/partial）
- data_flow 格式校验（仅格式，不校验业务内容）
- 超时检测（给 L1 发提醒，但 L1 裁决无时效约束）
- 死锁检测（有向图环检测，结果上报 L1）
- 金字塔汇报模板生成工具

**不提供**：
- 跨域任务的实际驱动执行
- 配合域的执行调度
- L1 裁决的替代

### 4.2 建造原则

1. **建造者/执行者分离**：IT 建完不能自己用，交给 L1 执行
2. **外部数据源优先**：优先从 GitHub 等外部数据源获取实现，外部无法满足时本地编写
3. **Soul Arbiter 审计**：所有代码交付前必须经过 Soul Arbiter 审计

---

## 5. 冲突解决

### 5.1 冲突类型与处理

| 类型 | 定义 | 处理 |
|------|------|------|
| 接口冲突 | 两个域输出字段同名但类型不同 | L1 裁决 |
| 依赖冲突 | 域A依赖域B输出但域B未完成 | L1 裁决 |
| 依赖死锁 | 有向依赖图中存在环 | IT 检测死锁 → **上报 L1 裁决** |
| 资源冲突 | 同一资源被两域同时使用 | L1 裁决 |
| 拒绝配合 | 配合域选择不参与 | 配合域向 L1 说明理由 → **L1 裁决** |

**核心原则**：所有冲突的裁决权归 L1，IT 仅检测和上报，不裁决。

### 5.2 L1 裁决权（无条件）

L1 的最终裁决权：
- **不受时效约束**：不存在"24小时无响应视为默认同意"等条款
- **是最终权力**：L1 裁决即终结，不存在上诉机制
- **以金字塔格式输出**：裁决结果按金字塔汇报格式输出

### 5.3 升级路径

```
域内问题 → L2 域自己处理
跨域冲突 → IT 检测上报 → L1 最终裁决
L1 裁决 → 终结，无上诉
```

---

## 6. 金字塔汇报强制

### 6.1 汇报结构

所有跨域协调结果必须按金字塔格式输出：

```yaml
pyramid_report:
  level_1_conclusion:      # 一句话结论（L1 视角）
    text: "<最终结论，不超过30字>"
    confidence: "high/medium/low"
  level_2_summary:         # 三句话摘要（L1 + L2 域联合视角）
    summary: ["<第1句>", "<第2句>", "<第3句>"]
    key_metrics:
      - metric: "<指标名>"
        value: "<值>"
        unit: "<单位>"
  level_3_detail:          # 附录/原始数据（可折叠）
    raw_outputs:
      <域>:
        status: "<域的输出状态>"
        output: "<原始输出>"
    technical_detail:
      - item: "<技术细节>"
        description: "<描述>"
    references:
      - type: "<数据源类型>"
        path: "<路径/URL>"
```

### 6.2 汇报责任人

| 阶段 | 汇报人 | 汇报给 |
|------|--------|--------|
| 配合域完成 | 配合域 | 主责域（直接传递） |
| 主责域完成 | 主责域 | L1 |
| L1 汇总 | L1 | 用户/L1 最终输出 |

---

## 7. Soul Arbiter 强制审计

### 7.1 审计触发点

| 触发时机 | 审计内容 |
|---------|---------|
| coordination_executor.py 建造完成 | 技术实现是否符合 SOUL.md 架构约束 |
| 协调协议版本变更 | 协议内容是否仍符合 SOUL.md |
| L2 域参与书签署 | 参与条件是否与协议一致 |
| 季度定期审计 | 协调系统运行是否符合 SOUL.md 原则 |

### 7.2 Soul Arbiter 审计结果

| 结果 | 含义 | 后续动作 |
|------|------|---------|
| PASS | 实现符合 SOUL.md | 继续执行 |
| FLAG | 有轻微偏差 | L1 知悉，继续执行 |
| BLOCK | 根本偏差 | 必须修改后才能继续 |
| ADVISORY | 建议改进 | L1 酌情决定 |

### 7.3 审计流程

```
建造完成 → Soul Arbiter 审计 → 结果记录
    ↓
    PASS/FLAG → 继续
    BLOCK → 修复 → 重新审计
    ADVISORY → L1 酌情
```

---

## 8. 退出机制

### 8.1 参与域退出

L2 域退出跨域协调：
- 向 L1 提交书面退出申请
- L1 在收到申请后**无时效约束地**给出最终裁决
- 退出后 30 天内完成已在途任务

### 8.2 IT 系统退出

IT 协调基础设施退出：
- L1 重新指定新的基础设施建造者
- 所有跨域协调链路暂停
- L1 直接接管协调执行直到新基础设施就绪

---

## 9. 签署机制

### 9.1 签署状态与约束力

| 域 | 签署状态 | 约束力 |
|----|---------|--------|
| IT | **已签署** | 协议对IT域立即生效 |
| investment | 待签署/自动接受 | 首次被指定为配合域时自动接受全部约束 |
| construction | 待签署/自动接受 | 首次被指定为配合域时自动接受全部约束 |
| ecommerce | 待签署/自动接受 | 首次被指定为配合域时自动接受全部约束 |
| game | 待签署/自动接受 | 首次被指定为配合域时自动接受全部约束 |
| life | 待签署/自动接受 | 首次被指定为配合域时自动接受全部约束 |
| multimodal | 待签署/自动接受 | 首次被指定为配合域时自动接受全部约束 |

**签署机制**：
- 已签署域：协议对该域立即生效
- 未签署域：首次被L1指定为配合域时，自动接受协议全部约束（L1协调执行令视为签署确认）
- 主动签署：域可通过向L1提交签署确认函主动完成签署

**配合义务**：
- 配合域收到L1协调执行令后，如无正当理由不得拒绝
- 配合域的`receive_data_flow()`方法视为接受约束的技术确认

### 9.2 生效条件

| 条款 | 条件 |
|------|------|
| 签署 | L1 签字 + IT 部门确认 + Soul Arbiter PASS 审计 |
| 生效 | 签署后立即生效 |
| 有效期 | 长期有效 |

### 9.3 修订流程（宪法修正案）

```
L1 提出修订 → 四顾问评审（仅参考） → Soul Arbiter 审计 → L1 最终决定
```

**注意**：四顾问评审是 L1 的参考，不是审批门禁。L1 有权在顾问反对的情况下基于其他考量决定是否修订。

---

## 附录A：当前参与域

| 域 | 签署状态 | 签署日期 |
|----|---------|---------|
| IT | **已签署** | 2026-05-15 |
| investment | 待签署/自动接受 | — |
| construction | 待签署/自动接受 | — |
| ecommerce | 待签署/自动接受 | — |
| game | 待签署/自动接受 | — |
| life | 待签署/自动接受 | — |
| multimodal | 待签署/自动接受 | — |

---

## 附录B：data_flow Schema

```yaml
"$schema": "hermes-coordination-v2"
type: object
required: [primary, inputs, outputs]
properties:
  primary:
    type: string
    description: 主责域名称
  supporting:
    type: array
    items: { type: string }
    description: 配合域列表
  inputs:
    type: object
    description: 各域的输入参数定义
  outputs:
    type: object
    description: 各域的输出定义
  status:
    type: string
    enum: [pending, in_progress, completed, error, partial]
  error:
    type: [string, object]
    description: 错误信息（string或结构化对象）
```

---

## 附录C：协调执行令模板（ISO标准）

```yaml
coordination_order:
  order_id: "L1-<YYYYMMDD>-<SEQ>"
  issued_by: "L1_CEO"
  issued_at: "<ISO8601时间戳>"
  task_summary: "<任务一句话描述>"
  primary_domain: "<主责域>"
  supporting_domains: ["<配合域>"]
  data_flow:
    inputs: {}
    outputs: {}
  pyramid_report_required: true
  l1_escalation: null     # 无时效约束
  soul_arbiter_audit: required
  version: "v2.1"          # Schema版本管理（向后兼容）
```

---

## 附录D：v2.1 修正案（2026-05-15）

### P0：裁决期间任务状态定义

**问题**：跨域任务在 L1 裁决期间，任务状态未定义。配合域可能已完成或失败，但主责域在等待 L1 裁决。此时整体任务状态不应标记为"进行中"、"失败"或"完成"，应为"暂停"。

**定义**：
- `status: PAUSED` — 任务在协调执行过程中，等待 L1 裁决
- 暂停期间：配合域已完成，主责域未执行，整体冻结
- L1 裁决后：根据裁决结果，状态转为 `completed`、`blocked` 或 `error`

**状态机**：
```
PENDING → ACTIVE（进入协调执行）
ACTIVE → PAUSED（L1裁决期间）
PAUSED → COMPLETED（L1批准）
PAUSED → BLOCKED（L1否决配合条件不满足）
PAUSED → ERROR（L1裁决时发现主责域执行异常）
```

**Soul Arbiter 审计要求**：协调执行令必须包含 `status` 字段，状态转换必须可追溯。

---

### P1-A：L1 授权委托机制

**背景**：L1 作为总路由中心，不可能所有任务都亲自裁决。对于简单、可预期的任务类型，L1 可主动授权给 L2 自主决策。

**授权原则**：
1. 授权是 L1 主动授予的有限权力，L1 可随时收回
2. 授权范围必须明确，超出范围的仍需 L1 裁决
3. 授权不等于弃权：L1 仍保留最终否决权

**授权清单（当前版本）**：

| 任务类型 | 授权范围 | 授权条件 |
|---------|---------|---------|
| 简单查询 | L2 可自主完成 | 复杂度 < 3，不涉及跨域 |
| 标准化报告 | L2 按模板生成 | 涉及 L2 专长领域 |
| IT 内部巡检 | it_orchestrator 自主完成 | 复杂度 < 5，不涉及跨域 |

**Soul Arbiter 审计要求**：`soul_arbiter_audit` 记录中增加 `delegation` 字段，标注是否在授权范围内执行。

**撤销机制**：L1 可随时撤销授权，撤销后该类任务自动恢复 L1 裁决路径。

---

### P1-B：新域加入机制

**背景**：Hermes 系统支持新 L2 域动态加入，无需修改 SOUL.md 核心原则。

**加入流程（5步）**：

```
Step 1 申请  →  新域向 L1 提交加入申请（含域定义、编排器路径、触发词）
Step 2 审计  →  Soul Arbiter 审计新域是否与 SOUL.md v3.x 核心原则冲突
Step 3 审批  →  L1 审批通过后，新域签署协调协议
Step 4 注册  →  新域注册到 L2_DOMAINS 和 L2_ORCHESTRATORS
Step 5 通告  →  向所有已有域通告新域加入
```

**Soul Arbiter 审计检查项**：
- 新域是否与现有 L2 域职责重叠（职责冲突检测）
- 新域编排器是否实现了必须接口（`orchestrate`、`receive_data_flow`）
- 新域是否接受协调协议所有约束

**回退机制**：新域加入后 30 天内为试用期，L1 可无条件撤销其参与资格。

#### P1-B 工程化实现

P1-B 流程已工程化，代码实现如下：

**代码位置**：

| 文件 | 职责 |
|------|------|
| `~/.hermes/scripts/l2_registry_loader.py` | P1-B 主实现：申请提交、状态机、注册写入、热reload |
| `~/.hermes/scripts/l2_domain_arbiter.py` | Soul Arbiter 审计器：FLAG/PASS/BLOCK 判定 |
| `~/.hermes/config/l2_domain_applications/` | P1-B 申请状态持久化目录（JSON文件） |

**CLI 命令参考**：

```bash
# 提交新域加入申请
python3 ~/.hermes/scripts/l2_registry_loader.py submit \
  --domain <域> \
  --orchestrator <编排器路径> \
  --label <标签> \
  --triggers <触发词（逗号分隔）>

# 查看所有申请状态
python3 ~/.hermes/scripts/l2_registry_loader.py applications

# Soul Arbiter 审计指定申请
python3 ~/.hermes/scripts/l2_domain_arbiter.py audit <application_id>

# 触发 L2 注册表热 reload（无需重启）
python3 ~/.hermes/scripts/l2_registry_loader.py reload
```

**申请状态机**：

```
PENDING → AUDITING → APPROVED/REJECTED → REGISTERED → NOTIFIED
                                         ↘ ROLLED_BACK（回退）
```

**热插拔验证案例 — game 域激活**：

game 域于 2026-05-15 完成首次热插拔验证，流程记录：
- 申请ID：`app-game-1778837042530`
- 审计结果：FLAG（协调协议尚未签署，但按自动接受机制处理）
- 审批结果：approved
- 试用期截止：2026-06-14
- 当前状态：`NOTIFIED`（已通告所有已有域）

---

### P2：Schema 版本管理

**目的**：协调执行令、Soul Arbiter 审计记录等数据结构增加 `version` 字段，便于前向兼容和审计追踪。

**版本规则**：
- 当前版本：`v2.1`
- 格式：`v{major}.{minor}`
- major 版本变更：数据结构不兼容，需要迁移脚本
- minor 版本变更：向后兼容，新增可选字段

**需要增加 version 字段的位置**：

| 文件/数据结构 | 当前状态 | 要求 |
|-------------|---------|------|
| 协调执行令（coordination_order） | 无 | 必须（v2.1 新增） |
| Soul Arbiter 审计记录 | 无 | 必须（v2.1 新增） |
| events.jsonl（gate_proposal_timeout） | 无 | 必须（v3.4 新增） |
| portfolios.db milestones | 无 | 可选 |

**向后兼容**：无 version 字段的旧记录视为 `v2.0`，解析器应能正确处理。

---

## 修订记录

|| 版本 | 日期 | 修订内容 |
||------|------|---------|
|| v2.2 | 2026-05-15 | **P1-B工程化**：附录D P1-B章节新增工程实现说明（代码位置/CLI命令/状态机/game域热插拔验证案例） |
|| v2.1 | 2026-05-15 | **P0裁决期间状态**定义PAUSED；**P1-A L1授权委托**明确清单与撤销机制；**P1-B新域加入**5步流程+Soul Arbiter审计+回退机制；**P2 Schema版本管理**所有数据结构增加version字段 |
| v1.0 | 2026-05-15 | 初始版本（已废弃：架构根本偏差，IT获未授权的执行权） |
| v2.0 | 2026-05-15 | 重建版本：基于SOUL.md v3.2五项约束重建（IT仅建造者+审计者、L1裁决权无条件、顾问仅为参考、金字塔汇报强制、Soul Arbiter强制审计） |
| v2.0 | 2026-05-15 | **正式签署生效**：三处格式修正（问题陈述/重复标题/附录A），IT域已签署（2026-05-15），其余6域自动接受约束 |
