# 画像合成报告

- candidates: 300
- valid: 258
- after_dedup: 258
- selected: 40
- target: 40
- off_label_hepatology: 7

## shortfall

- 无

## reject_reasons

- hard 难度需包含 traps 或打断习惯: 2
- hidden_objection 与 concerns 不相关（未命中任何关键词）: 38
- speech_habits 长度应为 4~80 字: 2

## dist_dept_diff

- cardiology/easy: 3
- cardiology/hard: 3
- cardiology/normal: 4
- endocrinology/easy: 6
- endocrinology/hard: 6
- endocrinology/normal: 8
- hepatology/easy: 3
- hepatology/hard: 3
- hepatology/normal: 4

## dist_style

- busy_efficient: 9
- conservative_habit: 8
- friendly_open: 7
- rigorous_evidence: 7
- skeptical_challenger: 9

## 生成统计

- batches: 65
- degraded_batches: 3
- budget_exceeded: False
- prompt_version: 0.1.0
