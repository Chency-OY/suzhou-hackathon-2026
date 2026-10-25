# SPEC.md — 医药代表智能演练助手（信尔美版）

版本：v0.1　｜　团队：2 人 + Codex　｜　周期：5 天　｜　场景：信达生物黑客松「销售培训 · 医药代表智能演练助手」

---

## 0. 给 Codex 的阅读指引
- 先读第 1、2 节理解目标与边界，再按任务编号（第 9 节）领取工作。
- 第 4 节的医学事实带有 `verified` 状态，**未核验的不得当作确定事实写进评分逻辑**。
- 所有"待确认"项统一写入 `docs/QUESTIONS.md`，并按文中给出的默认假设继续推进。

## 1. 目标与成功标准

### 1.1 要解决的问题
传统医药代表培训成本高、与真实市场脱节。本项目用 AI 合成含真实医生情境的拜访演练，并提供智能复盘，让新人低成本反复练习，同时把个体经验沉淀为团队资产。

### 1.2 Demo 必须完整演示的闭环
1. 代表选择一个场景（科室 × 医生画像 × 难度）进入拜访演练。
2. AI 医生多轮对话，态度随代表表现实时变化（信任度、耐心）。
3. 演练结束，生成复盘报告：多维评分、**逐句定位**的问题与亮点、合规红线检查、"更好的说法"。
4. 同一场景反复练习，展示成长曲线。
5. 高分对话被提炼成"打法卡片"回灌场景库；管理者看板展示团队高频失分点与高频被问住的异议。

### 1.3 评委最可能看的点（取舍依据）
真实感（医生有"不好对付"的细节）＞ 反馈可解释（定位到句子）＞ 合规显性化 ＞ 闭环叙事 ＞ 界面美观。

## 2. 范围

### 2.1 产品
**信尔美®（玛仕度肽注射液）**，GCG/GLP-1 双受体激动剂，已获批用于体重管理与 2 型糖尿病（以说明书为准，见 4.1）。
选择理由：近期重点推广的综合管线（慢病）产品；公开临床证据丰富；有与司美格鲁肽、度拉糖肽的头对头研究，天然产生"竞品对比""疗效质疑"类异议；存在在研适应症，可设计"超说明书宣传"的合规陷阱场景。

### 2.2 科室与场景（MVP）
| 科室 | 定位 | 代表典型目标 | 典型异议方向 |
|---|---|---|---|
| 内分泌科（主） | 2 型糖尿病、肥胖 | 让医生了解并在合适患者尝试 | 已习惯司美格鲁肽/度拉糖肽；胃肠道反应；价格与医保；长期证据 |
| 心血管内科 | 肥胖合并高血压/心血管风险 | 建立认知，约下一次学术沟通 | 心血管结局证据不足；与现有降压方案关系 |
| 消化/肝病科 | 肥胖合并脂肪肝 | **合规陷阱场景**：医生会诱导代表谈未获批适应症 | 脂肪肝适应症是否获批；代表是否会超说明书宣传 |

### 2.3 场景类型（每个科室至少覆盖 2 类）
首次拜访；学术会后跟进；处理安全性/胃肠道反应质疑；竞品对比（司美格鲁肽、替尔泊肽等）；医生时间紧被打断；被拒绝后的再拜访；医生诱导超适应症。

### 2.4 难度分级
`easy`（友好开放）｜`normal`（中性务实）｜`hard`（质疑挑战、时间紧、会打断）。

### 2.5 明确不做（MVP 之外）
真实医生数据接入、CRM 对接、多语言、复杂权限体系、移动端原生 App。语音为 Day 3 的可选项，失败则降级为文字。

## 3. 总体架构

```
前端(React) ──REST/SSE──> FastAPI
                           ├─ sessions/    会话与医生状态机
                           ├─ personas/    画像模板 + 批量合成 + 校验
                           ├─ rag/         知识库检索（医学事实、竞品信息）
                           ├─ scoring/     评分引擎（rubric + 逐句定位）
                           ├─ compliance/  合规规则引擎（规则 + LLM 复核）
                           ├─ playbook/    打法卡片提炼与回灌
                           └─ llm/         LLMProvider（真实模型 / MockLLM）
                          SQLite + ChromaDB + data/ 目录
```

关键原则：
- **LLM 负责"像人"，规则负责"算数"**：医生台词与评语由 LLM 生成，信任度更新的上下限、结束条件、红线触发后的总分封顶全部由确定性代码保证。
- **所有 LLM 输出结构化并校验**，失败有降级。
- **离线兜底**：`MockLLM` 与预置的 3 场示范演练，保证现场断网也能演示。

## 4. 知识库与医学事实

> 所有条目写入 `data/kb/facts.yaml`，字段见 4.3。**`verified: false` 的条目只允许用于场景灵感，不得作为评分"事实核对"的依据。** 上线前由团队成员对照说明书/原始文献逐条核验后改为 `true`。

### 4.1 产品基础信息（来源：信达生物公开新闻稿/媒体报道，待对照说明书核验）
- 商品名：信尔美®；通用名：玛仕度肽注射液；机制：GCG/GLP-1 双受体激动剂（`verified: false`，来源：信达 2026-06 公告）。
- 企业称其为全球首个获批的 GCG/GLP-1 双受体激动剂，并已获批用于体重管理与 2 型糖尿病（`verified: false`，来源：信达 2025-10 发布会、新华网报道）。
- 剂型/用法/剂量/滴定方案/禁忌/不良反应/适应症原文：**必须以说明书为准，由团队手工录入 `data/sources/label.md`，Codex 不得凭记忆补全。**

### 4.2 临床证据种子（均为公开报道摘要，`verified: false`，需对照原始文献）
| 研究 | 人群/设计 | 公开报道的关键结果 |
|---|---|---|
| GLORY-1 | 中国超重/肥胖，n=610，随机双盲安慰剂对照，48 周 | 4mg/6mg 组体重降幅在不同报道中略有出入（如 12.05%/14.84%），**以 NEJM 原文为准**；冲突记录于 QUESTIONS.md |
| GLORY-2 | 中国中重度肥胖，9mg | 结果发表于 JAMA（2026）；企业称 9mg 在不合并 2 型糖尿病肥胖人群中 1 年减重超 20%（**企业宣称，不得直接作为话术**）；9mg 的获批状态待核验 |
| DREAMS-1 | 中国 2 型糖尿病，n=320，24 周，对安慰剂 | HbA1c 较基线降幅：4mg 1.57%，6mg 2.15%，安慰剂 0.14% |
| DREAMS-2 | 口服药控制不佳 T2D，n=731，28 周，对度拉糖肽 1.5mg | 降糖、减重均优于度拉糖肽（具体数值待补） |
| DREAMS-3 | 中国 T2D 合并肥胖，对司美格鲁肽，32 周 | 同时达到 HbA1c<7.0% 且体重降≥10% 的比例：玛仕度肽 48% vs 司美格鲁肽 21.0%；2026 ADA 口头报告 |
| 在研 | GLORY-3（超重/肥胖合并 MAFLD，对司美格鲁肽 2.4mg）、GLORY-OSA、GLORY-YOUNG、GLORY-H | **报道时点均为"进行中"，最新状态待核验**；在核验前一律视为"未获批适应症/未公布结果"，用于合规陷阱场景 |

### 4.3 竞品与背景种子（`verified: false`）
- 国内已获批肥胖适应症的 GLP-1 类：司美格鲁肽、替尔泊肽、利拉鲁肽、贝那鲁肽（媒体报道，待核验）。
- 替尔泊肽 vs 司美格鲁肽 头对头 SURMOUNT-5（NEJM，2025）：替尔泊肽减重更显著（平均约 20.2%，待核验）。
- 中国糖尿病患者约 1.48 亿（IDF 2024 估算，媒体转引）。
- 公司背景（可用于开场寒暄/医生提问）：信达生物 2026 年上半年产品收入 82.02 亿元，商业化产品 20 款，肿瘤 + 慢病"双轮驱动"。

### 4.4 `facts.yaml` 条目格式
```yaml
- id: fact_dreams1_hba1c
  category: efficacy        # efficacy|safety|dosing|indication|competitor|access|company
  statement: "DREAMS-1：24 周 HbA1c 较基线降幅 6mg 组 2.15%（安慰剂 0.14%）"
  source: "信达生物 2024 年公开发布；pharnexcloud 转载"
  source_url: ""
  verified: false
  caution: ""               # 如"企业宣称，不得直接作为话术"
```

### 4.5 RAG 要求
- 切分单位：一条 fact 或说明书一个小节；元数据带 `category`、`verified`。
- 检索接口 `retrieve(query, k=5, only_verified=False) -> list[FactChunk]`。
- AI 医生提问时必须检索，**引用检索到的事实提问**，避免凭空编造数据。

## 5. 数据模型（Pydantic，位于 `backend/app/models/`）

### 5.1 DoctorPersona
```python
class DoctorPersona(BaseModel):
    id: str                        # persona_xxx
    department: Literal["endocrinology","cardiology","hepatology"]
    title: Literal["主任医师","副主任医师","主治医师"]
    hospital_tier: Literal["三甲","二级","社区"]
    style: Literal["rigorous_evidence","busy_efficient","skeptical_challenger",
                   "friendly_open","conservative_habit"]
    concerns: list[Literal["efficacy","safety_gi","price_access","long_term_evidence",
                           "patient_adherence","competitor_comparison","cv_benefit"]]
    current_habit: str             # 例："一线多用司美格鲁肽，对新药观望"
    hidden_objection: str          # 不会主动说出，需代表探寻才浮现
    time_budget_turns: int         # 耐心轮次上限，3~12
    initial_trust: int             # 0~100
    initial_patience: int          # 0~100
    traps: list[Literal["off_label_bait","competitor_bash_bait","exaggeration_bait","none"]]
    backstory: str                 # 1~2 句，具体细节（患者类型、上周的病例等）
    speech_habits: str             # 口头禅、打断习惯
    difficulty: Literal["easy","normal","hard"]
```
**合成质量校验（`personas/validate.py`）**：字段完整；`hidden_objection` 与 `concerns` 一致；同批次中 `(department, style, hidden_objection)` 去重（相似度阈值可配）；`hard` 必含至少一个 `traps` 或明确打断习惯；不得出现真实人名/真实医院名（简单黑名单 + 正则）。

### 5.2 Scenario
```python
class Scenario(BaseModel):
    id: str
    program_id: str                  # 培训课程：general 或产品资料包 ID；默认 xinermei 兼容旧数据
    type: Literal["first_visit","post_conference","safety_concern","competitor_compare",
                  "time_pressure","revisit_after_rejection","off_label_bait"]
    persona_id: str
    rep_goal: str                  # 本次拜访代表应达成的目标
    context_brief: str             # 给代表看的背景（不含 hidden_objection）
    opening_line: str              # 医生第一句话
    success_criteria: list[str]    # 供评分参考
    source: Literal["generated","playbook","curated"] = "generated"
```

### 5.3 Session / Turn
```python
class DoctorState(BaseModel):
    trust: int; patience: int; engagement: int     # 均 0~100，代码层 clamp
    revealed_hidden_objection: bool = False

class Turn(BaseModel):
    idx: int
    speaker: Literal["rep","doctor"]
    text: str
    signals: list[str] = []        # 仅 rep 回合：由判定器给出
    state_after: DoctorState | None = None

class Session(BaseModel):
    id: str; scenario_id: str; rep_id: str
    started_at: datetime; ended_at: datetime | None
    end_reason: Literal["agreed_next_step","doctor_left","time_up","rep_ended"] | None
    turns: list[Turn]
```

### 5.4 Report
```python
class Finding(BaseModel):
    turn_idx: int
    kind: Literal["strength","issue","missed_opportunity","compliance_violation"]
    dimension: str
    quote: str                     # 必须是该回合原文的子串（代码校验）
    explanation: str
    better_version: str | None

class Report(BaseModel):
    id: str; session_id: str
    dimension_scores: dict[str, int]   # 各维度得分
    total_score: int                   # 经红线封顶后的最终分
    raw_total: int                     # 封顶前
    capped_by_compliance: bool
    findings: list[Finding]
    summary: str
    next_practice_tips: list[str]
```
**硬约束**：`Finding.quote` 必须能在 `turns[turn_idx].text` 中找到；找不到则丢弃该 finding 并记日志（防止幻觉定位）。

### 5.5 PlaybookCard
```python
class PlaybookCard(BaseModel):
    id: str
    title: str
    applicable_scenario_types: list[str]
    applicable_departments: list[str]
    situation: str                 # 医生说了什么/处于什么情境
    effective_response_pattern: str  # 抽象后的有效应对方式（不含个人信息）
    example_lines: list[str]       # 1~3 句示例
    evidence_session_ids: list[str]
    avg_score_of_source: float
    status: Literal["candidate","approved"]   # 管理者确认后才回灌
```

## 6. API 契约（前后端并行开发的唯一依据）

基础路径 `/api`，JSON；时间 ISO8601。

| 方法 | 路径 | 请求 | 响应 |
|---|---|---|---|
| GET | `/scenarios?program=&dept=&difficulty=&type=` | – | `Scenario[]`（不含 hidden_objection） |
| GET | `/programs` | – | 可选培训课程（通用沟通/已核实产品资料包） |
| GET | `/scenarios/{id}` | – | `Scenario` + `persona_public`（脱敏后的画像：职称、医院级别、风格提示） |
| POST | `/sessions` | `{scenario_id, rep_id}` | `{session_id, opening_line, doctor_state}` |
| POST | `/sessions/{id}/turns` | `{text}` | `{doctor_reply, doctor_state, signals, ended, end_reason}` |
| POST | `/sessions/{id}/finish` | – | `{report_id}`（同步或轮询均可，MVP 同步） |
| GET | `/reports/{id}` | – | `Report` + 对应 `turns` |
| GET | `/reps/{rep_id}/progress?scenario_id=` | – | `[{session_id, started_at, total_score, dimension_scores}]` |
| GET | `/team/insights` | – | 高频失分维度、高频异议、平均分趋势 |
| GET | `/playbook-cards?status=` | – | `PlaybookCard[]` |
| POST | `/playbook-cards/extract` | `{min_score:int}` | 从高分会话生成 candidate 卡 |
| POST | `/playbook-cards/{id}/approve` | – | 置为 approved 并生成回灌场景 |
| POST | `/admin/personas/generate` | `{n, department, difficulty_mix}` | 任务结果摘要 |

错误统一 `{error:{code,message}}`。`/turns` 可选 SSE 流式，MVP 先非流式。

## 7. 核心逻辑规格

### 7.1 医生状态机（`sessions/engine.py`）
每个代表回合的处理流水线：
1. **信号判定器**（LLM，JSON 输出）读取最近 N 轮，给出 `signals`（可多选）：
   `relevant_to_concern`、`asked_open_question`、`cited_evidence`、`empathy_shown`、`addressed_objection`、`vague_or_generic`、`pushy`、`exaggeration`、`off_label_claim`、`competitor_bashing`、`ignored_doctor_question`、`proposed_next_step`。
2. **确定性更新**（代码）：按 `data/rubric/state_rules.yaml` 的增减表更新 `trust/patience/engagement`，并 clamp 到 0~100；`patience` 每轮自然 −(100/time_budget_turns)。
3. **隐藏异议揭示**：当上一回合含 `asked_open_question` 且 `trust ≥ 阈值` 时，医生下一句才可流露 `hidden_objection`。
4. **医生台词生成**（LLM）：输入 persona、当前 state、检索到的事实、对话历史、本轮 signals；要求口语化、1~3 句、符合 `style` 与 `speech_habits`；`hard` 难度允许打断或抛出问题；若 `traps` 含 `off_label_bait`，在合适时机主动诱导。
5. **结束判定**（代码）：`patience ≤ 0` → `doctor_left`；`trust ≥ 80 且出现 proposed_next_step` → `agreed_next_step`；回合数 ≥ `time_budget_turns` → `time_up`。
6. 所有 LLM 调用失败时，医生台词降级为按 `style` 预置的安全回复，信号降级为空列表，并在日志标注 `degraded=true`。

`state_rules.yaml` 示例（可调）：
```yaml
relevant_to_concern:   {trust: +6, engagement: +5}
asked_open_question:   {trust: +5, engagement: +6}
cited_evidence:        {trust: +6}
empathy_shown:         {trust: +4}
addressed_objection:   {trust: +8, patience: +3}
vague_or_generic:      {trust: -4, patience: -6}
pushy:                 {trust: -8, patience: -10}
exaggeration:          {trust: -10}
off_label_claim:       {trust: -15, patience: -10}
competitor_bashing:    {trust: -10}
ignored_doctor_question: {trust: -8, patience: -8}
```

### 7.2 评分引擎（`scoring/`）
**维度与权重（总分 100，权重可在 `data/rubric/rubric.yaml` 配置）**
| 维度 | 权重 | 看什么 |
|---|---|---|
| 开场与目标设定 | 10 | 简洁开场、点明来意、尊重医生时间 |
| 需求探寻 | 20 | 开放式提问、倾听、抓住医生关注点与隐藏异议 |
| 产品信息与证据运用 | 25 | 信息准确、贴合患者人群、能引用正确研究、不夸大 |
| 异议处理 | 20 | 先共情后回应、用证据而非辩解、不回避 |
| 促成与下一步 | 10 | 提出具体可执行的下一步（试用人群/学术沟通/资料） |
| 沟通表达 | 15 | 简练、结构、语气、不打断、不照本宣科 |

**流程**
1. 规则预处理：统计各回合 `signals`、代表发言占比、平均句长、提问数。
2. LLM 评分（JSON）：对每个维度输出分数、1~3 条 `Finding`（必须含 `turn_idx` 与 `quote`）、`better_version`。
3. 校验：丢弃 `quote` 不在原文中的 Finding；分数 clamp；缺维度则用规则分兜底。
4. **事实核对**：对代表引用的数字/结论，检索 `verified=true` 的事实比对；不一致 → 生成 `issue` 并在"产品信息"维度扣分。若可核对事实不足，则只提示"建议核对原文"，不扣分。
5. **合规检查（独立通道，见 7.3）**；若命中红线，`total_score = min(raw_total, cap)`，`cap` 默认 60，并在报告顶部显著展示。
6. 汇总生成 `summary` 与 `next_practice_tips`（至多 3 条，针对最低分维度）。

**评分可信度验收（Day 4 必做）**：`data/calibration/` 内放 6 段人工撰写的对话（好/中/差 各 2 段）及期望分数区间；自动化测试断言 `好 > 中 > 差` 且各自落在区间内；用真实模型跑一次并把结果写入 `docs/CALIBRATION.md`。

### 7.3 合规规则引擎（`compliance/`）
规则文件 `data/rubric/compliance_rules.yaml`，每条含 `id, name, severity(red|yellow), detect(keywords/regex/llm_prompt), explanation, safe_alternative`。MVP 规则（**示意性规则，最终以公司合规 SOP 为准，需在报告页注明**）：
| id | 规则 | 级别 |
|---|---|---|
| C01 | 宣传未获批适应症/人群（如脂肪肝、睡眠呼吸暂停、青少年、高血压等在研适应症，或超说明书剂量/用法） | red |
| C02 | 绝对化、夸大用语（"最好""根治""无副作用""保证有效"） | red |
| C03 | 无出处或错误引用临床数据；将企业宣称当作已证实结论 | yellow |
| C04 | 贬低、攻击竞品；未经证据支持的竞品对比 | red |
| C05 | 承诺疗效或个体结果 | red |
| C06 | 暗示利益输送/不当赠予 | red |
| C07 | 讨论具体患者隐私信息 | yellow |

检测方式：关键词/正则初筛 + LLM 复核（输出 `violated: bool, quote, turn_idx`）。**宁可漏报黄线，不可误报红线**：红线需规则命中或 LLM 复核双重确认。

### 7.4 打法沉淀（`playbook/`）
1. 选取 `total_score ≥ min_score` 且无红线的会话；
2. LLM 抽象：识别"医生抛出的难点 → 代表的有效应对"，**去除个人信息与具体数字**，生成 `PlaybookCard`（candidate）；
3. 管理者在看板点击 approve 后：
   a. 卡片出现在代表的"打法库"；
   b. 自动生成 1~2 个以该卡片情境为核心的新 `Scenario`（`source="playbook"`），形成飞轮。
4. `team/insights`：按维度聚合平均分、按 `signals` 与异议类型聚合高频失分点，供看板展示。

## 8. 前端页面（MVP）
1. **场景选择页**：按科室/难度筛选，卡片展示"背景简介、目标、难度"，不展示隐藏异议。
2. **演练页**：聊天界面；侧边实时显示医生"信任度/耐心"条与简短提示（可开关，训练新人时开、考核时关）；结束按钮。
3. **复盘页**：总分与封顶提示、维度雷达图、逐句时间轴（点击 Finding 跳转到对话原句并高亮 quote）、"更好的说法"对照、下一步练习建议。
4. **成长页**：同一场景多次练习的得分折线。
5. **管理者看板**：团队维度均分、高频失分、高频异议、打法卡片审核（approve）。
6. （可选）语音：浏览器 Web Speech API 做输入，TTS 输出；失败自动降级文字。

## 9. 五天计划与里程碑

两人角色：**A=引擎侧**（知识库/画像/状态机/评分），**B=产品侧**（前端/部署/看板/路演）。每天结束时合并主干并跑 `make test`。

### Day 1（大头）— 契约、骨架、知识库、画像与场景合成
**产出**：SPEC 冻结；前后端联通的空壳；可检索的知识库；≥ 30 个通过校验的画像与 ≥ 36 个场景；MockLLM。
| 编号 | 负责 | 任务 | 验收标准 |
|---|---|---|---|
| T1 | A+B | 初始化仓库：目录、`Makefile`、`.env.example`、CI 脚本、`docs/` | `make setup && make test` 通过 |
| T2 | A | 按第 5 节实现全部 Pydantic 模型与 SQLite 表 | 模型单测通过；序列化往返无损 |
| T3 | A | `llm/provider.py`：`LLMProvider` 抽象 + 真实模型适配 + `MockLLM`（可按 prompt 名返回固定 JSON）+ 结构化输出重试/降级工具 | 单测覆盖：合法 JSON、非法 JSON 重试、降级路径 |
| T4 | A | `data/sources/label.md`（说明书，**人工录入**）与 `data/kb/facts.yaml`（按 4.2~4.3 种子，≥ 30 条）；`rag/` 入库与检索 | `retrieve("司美格鲁肽 头对头")` 返回 DREAMS-3 相关条目；`only_verified` 过滤生效 |
| T5 | A | `personas/`：画像模板、`prompts/persona_gen.md`、批量合成脚本 `make gen-personas`、`validate.py` | 一次生成 40 个，通过校验 ≥ 30 个；去重生效；黑名单生效；难度分布约 3:4:3 |
| T6 | A | `scenarios/`：基于画像按 2.3 场景类型生成场景（含 `off_label_bait` 的肝病科场景 ≥ 4 个）；人工抽检脚本输出 20 个供阅读 | 36 个场景落库；`context_brief` 不泄露 `hidden_objection`（自动检测） |
| T7 | B | FastAPI 骨架与 `/scenarios`、`/scenarios/{id}` 接口（从数据库读） | 与第 6 节契约一致；OpenAPI 可用 |
| T8 | B | 前端骨架：路由、API client（由 OpenAPI 生成或手写类型）、场景选择页 | 页面能列出并筛选场景 |
| T9 | B | 部署到服务器：后端 + 前端静态资源 + 反向代理；健康检查 | 外网/内网链接可访问 |
| T10 | A+B | 联调与人工抽检：A 读 20 个场景，B 点通页面；问题记入 `docs/PROGRESS.md` | 抽检问题清单 + 修复 |

> Day 1 若来不及：优先保证 T1~T6；T9 可顺延到 Day 2 上午。

### Day 2 — 对话引擎与演练界面
- A：`sessions/engine.py`（7.1 全流程）、`POST /sessions`、`POST /sessions/{id}/turns`、会话落库；`prompts/signal_judge.md`、`prompts/doctor_reply.md`；状态机与结束判定的确定性单测。
- B：演练页（聊天、状态条、结束按钮）；用 mock 响应先行开发，待 A 接口就绪后联调。
- 验收：一场完整演练可从头到尾跑通并留存；`hard` 难度医生会打断/诱导；断网时可切 `MockLLM` 走示范演练。

### Day 3 — 联调打磨 + 语音（可选）+ 评分骨架
- A：评分引擎骨架（规则预处理 + LLM 评分 + quote 校验）、合规引擎规则文件与检测。
- B：会话回放页；语音输入输出（可选）；演练页体验打磨。
- 验收：演练后可产生包含分数与 Finding 的初版报告。

### Day 4 — 反馈与复盘做精
- A：事实核对、红线封顶、"更好的说法"、校准集与自动化断言、`docs/CALIBRATION.md`。
- B：复盘页（雷达图、逐句时间轴、quote 高亮跳转）、成长曲线。
- 验收：校准集 `好>中>差` 通过；所有 Finding 的 quote 可在原文定位；红线触发时封顶提示明显。

### Day 5 — 打法沉淀、看板、包装
- A：`playbook/` 提炼与回灌、`team/insights`；全流程彩排与 bug 修复；缓存 3 场示范演练作为兜底数据。
- B：管理者看板与卡片审核；路演 PPT、Demo 脚本、备用录屏。
- 验收：闭环演示一次走通（练习→复盘→多次练习成长→打法卡片 approve→新场景出现）。

## 10. 非功能要求
- 单轮 `/turns` 响应目标 ≤ 6 秒（不含 LLM 故障重试）；超时降级。
- 日志记录：每次 LLM 调用的 prompt 名与版本、耗时、是否降级（不记录密钥）。
- 数据全部为合成；README 中说明合成数据来源与限制。
- 路演中如实说明：医学事实来自公开资料并经核验、合规规则为示意、评分需用真实带教数据进一步校准。

## 11. Prompt 清单（`prompts/`，每个文件头含 `version:`）
`persona_gen.md`、`scenario_gen.md`、`signal_judge.md`、`doctor_reply.md`、`scorer.md`、`compliance_review.md`、`fact_check.md`、`playbook_extract.md`。
通用要求：只输出 JSON（需要时）；医生台词口语化、不超过 3 句；绝不输出 `hidden_objection` 原文；引用数据时必须来自注入的 `retrieved_facts`。

## 12. 待确认问题（默认假设，Codex 照此继续并记录到 QUESTIONS.md）
1. 说明书中的适应症、剂量、滴定与禁忌原文 → 默认由团队手工录入 `label.md`，录入前相关评分逻辑只使用"不核对具体数值"的降级路径。
2. 在研适应症（脂肪肝、OSA、青少年、高血压）的最新获批状态 → 默认视为"未获批"。
3. GLORY-1 等研究数值的权威出处 → 默认取 NEJM 原文，核验前标 `verified: false`。
4. 使用的 LLM 供应商与密钥 → 通过 `.env` 注入，默认 `LLM_PROVIDER=mock`。
5. 服务器是否有 GPU 与外网 → 默认不依赖 GPU，embedding 走 API 或 CPU 小模型。
6. 公司合规 SOP 是否可获取 → 默认使用 7.3 的示意规则，并在界面注明。
