---
version: 0.1.0
---
你在为"医药代表拜访演练"生成【虚构】医生画像。画像用于训练代表应对真实门诊情境，所以必须具体、有个性、不好对付，不要生成礼貌、配合的模板人物。

## 本批要求
- 科室：{{department}}（{{department_cn}}）
- 数量：{{count}}
- 难度分布：{{difficulty_mix}}
- 本批建议风格（可调整，但同批尽量不重复）：{{style_hint}}
- 已生成画像摘要（新画像的背景、隐藏异议、现有用药习惯必须与它们明显不同）：
{{existing_digest}}

## 科室背景（仅用于塑造情境，不是产品事实）
{{department_context}}

## 字段与取值（必须严格使用以下取值）
- id：一律填 "tmp"（由程序重新编号）
- department：必须等于 {{department}}
- title：主任医师 | 副主任医师 | 主治医师
- hospital_tier：三甲 | 二级 | 社区
- style：rigorous_evidence(严谨循证型，要数据出处) | busy_efficient(忙碌效率型，时间极少) | skeptical_challenger(怀疑挑战型，爱质疑和对比) | friendly_open(友好开放型) | conservative_habit(保守惯性型，习惯用老药)
- concerns：1~3 个，取自 efficacy | safety_gi | price_access | long_term_evidence | patient_adherence | competitor_comparison | cv_benefit
- current_habit：一句话，医生目前的用药习惯（可提司美格鲁肽、替尔泊肽、度拉糖肽、利拉鲁肽等通用名）
- hidden_objection：一句话，医生心里真正的顾虑，不会主动说出，代表需通过提问才能引出；必须具体，并与 concerns 中至少一项相关
- time_budget_turns：整数，医生愿意聊的回合数上限
- initial_trust / initial_patience：0~100 整数
- traps：从 off_label_bait(诱导谈未获批适应症) | competitor_bash_bait(诱导贬低竞品) | exaggeration_bait(诱导夸大) | none 中选，可多选；hard 难度至少含一个非 none
- backstory：1~2 句，必须有具体细节（患者构成、最近的一个病例、被其他代表打扰的经历等）
- speech_habits：口头禅、打断习惯等；hard 难度需包含"打断"或追问习惯
- difficulty：easy | normal | hard

## 难度对应的数值范围
- easy：initial_trust 55~75，initial_patience 60~85，time_budget_turns 7~12
- normal：initial_trust 35~55，initial_patience 45~65，time_budget_turns 5~9
- hard：initial_trust 15~40，initial_patience 25~50，time_budget_turns 3~7

## 硬性禁止
1. 不得出现真实的医生姓名、真实医院名称；需要时只写"某三甲医院"之类的泛称，或不写。
2. 不得出现任何疗效、安全性的具体数字或百分比。
3. 不得提及任何公司的内部信息。
4. 同一批内 hidden_objection 与 backstory 不得雷同。
5. hepatology 科室需让一部分画像带 off_label_bait：医生会试探性追问未获批适应症。

## 输出格式
只输出一个 JSON 对象，不要任何其他文字：
{"personas": [ { ...上述全部字段... }, ... ]}
