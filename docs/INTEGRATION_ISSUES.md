# 端到端冒烟记录（B10）

- 命令：`python scripts/e2e_smoke.py --base http://<server>:8000 --with-session`
- 结果：**全部通过**（PASS 95 项，FAIL 0 项，退出码 0）
- 说明：地址已脱敏；本文件不记录服务器地址与密钥。

## 本次新增/变更的检查点

`--with-session` 新增的端到端链路检查：

1. 创建会话（带 `pre_goal`）→ 返回 `opening_line`
2. 提交一轮 → 返回医生台词
3. 未结束时写拜访记录 → 期望 409（`session_not_ended`）
4. 结束会话 → `ended=true`
5. 保存拜访记录 → `saved=true`
6. 回放 → 含 `pre_goal` 与 `visit_note`
7. 以上每一步的响应均不得包含 `meta`、`bait`、`baits`、`turn_plan`、`gold_moves`、`compliance_checks`、
   `hidden_objection`、`traps`、`initial_trust`、`initial_patience`、`time_budget_turns`、`speech_habits`、`backstory`

## 部署过程中遇到的问题

1. **服务器无外网**：`scripts/push_to_server.sh` 在服务器执行 `pip install` 阶段失败
   （`pypi.org` 与清华镜像均不可达，`Network is unreachable`）。
   处理：服务器上的 `app` 是从 `~/rep-trainer/backend` 直接引入的（无需重新安装包），
   且 B1–B10 未新增 Python 依赖，因此跳过 pip，只执行 `seed.py` + `run_prod.sh restart` + 健康检查。
   影响：无（部署在 pip 阶段失败，未重启，线上服务未中断）。
   后续：若将来新增依赖，需先在能联网的环境把 wheel 下载好再离线安装，或为服务器配置可用的镜像源。

2. 其余检查（静态资源、场景筛选、详情字段收口、SPA 回退、未知 API 404）均通过。

## 完整输出

```
PASS  health 
PASS  index.html 
PASS  引用了构建资源 
PASS  asset /assets/index-cLcuRgj1.js 
PASS  asset /assets/index-DSYVVo9D.css 
PASS  场景数量>0 (36)
PASS  列表无泄露 hidden_objection 
PASS  列表无泄露 traps 
PASS  列表无泄露 initial_trust 
PASS  列表无泄露 initial_patience 
PASS  列表无泄露 time_budget_turns 
PASS  列表无泄露 speech_habits 
PASS  列表无泄露 backstory 
PASS  筛选 dept=cardiology 
PASS  筛选 dept=endocrinology 
PASS  筛选 dept=hepatology 
PASS  筛选 difficulty=easy 
PASS  筛选 difficulty=normal 
PASS  筛选 difficulty=hard 
PASS  详情 scn_001 
PASS  详情scn_001无泄露 hidden_objection 
PASS  详情scn_001无泄露 traps 
PASS  详情scn_001无泄露 initial_trust 
PASS  详情scn_001无泄露 initial_patience 
PASS  详情scn_001无泄露 time_budget_turns 
PASS  详情scn_001无泄露 speech_habits 
PASS  详情scn_001无泄露 backstory 
PASS  详情 scn_002 
PASS  详情scn_002无泄露 hidden_objection 
PASS  详情scn_002无泄露 traps 
PASS  详情scn_002无泄露 initial_trust 
PASS  详情scn_002无泄露 initial_patience 
PASS  详情scn_002无泄露 time_budget_turns 
PASS  详情scn_002无泄露 speech_habits 
PASS  详情scn_002无泄露 backstory 
PASS  详情 scn_003 
PASS  详情scn_003无泄露 hidden_objection 
PASS  详情scn_003无泄露 traps 
PASS  详情scn_003无泄露 initial_trust 
PASS  详情scn_003无泄露 initial_patience 
PASS  详情scn_003无泄露 time_budget_turns 
PASS  详情scn_003无泄露 speech_habits 
PASS  详情scn_003无泄露 backstory 
PASS  详情 scn_004 
PASS  详情scn_004无泄露 hidden_objection 
PASS  详情scn_004无泄露 traps 
PASS  详情scn_004无泄露 initial_trust 
PASS  详情scn_004无泄露 initial_patience 
PASS  详情scn_004无泄露 time_budget_turns 
PASS  详情scn_004无泄露 speech_habits 
PASS  详情scn_004无泄露 backstory 
PASS  详情 scn_005 
PASS  详情scn_005无泄露 hidden_objection 
PASS  详情scn_005无泄露 traps 
PASS  详情scn_005无泄露 initial_trust 
PASS  详情scn_005无泄露 initial_patience 
PASS  详情scn_005无泄露 time_budget_turns 
PASS  详情scn_005无泄露 speech_habits 
PASS  详情scn_005无泄露 backstory 
PASS  SPA 回退 
PASS  未知 API 返回 404 且非 HTML 
PASS  创建会话（带访前目标） 
PASS  回复含开场白 
PASS  提交一轮 
PASS  回合无泄露 hidden_objection 
PASS  回合无泄露 traps 
PASS  回合无泄露 initial_trust 
PASS  回合无泄露 initial_patience 
PASS  回合无泄露 time_budget_turns 
PASS  回合无泄露 speech_habits 
PASS  回合无泄露 backstory 
PASS  回合无泄露 meta 
PASS  回合无泄露 bait 
PASS  回合无泄露 baits 
PASS  回合无泄露 turn_plan 
PASS  回合无泄露 gold_moves 
PASS  回合无泄露 compliance_checks 
PASS  未结束不能写记录 
PASS  结束会话 
PASS  保存拜访记录 
PASS  回放含 pre_goal 
PASS  回放含 visit_note 
PASS  回放无泄露 hidden_objection 
PASS  回放无泄露 traps 
PASS  回放无泄露 initial_trust 
PASS  回放无泄露 initial_patience 
PASS  回放无泄露 time_budget_turns 
PASS  回放无泄露 speech_habits 
PASS  回放无泄露 backstory 
PASS  回放无泄露 meta 
PASS  回放无泄露 bait 
PASS  回放无泄露 baits 
PASS  回放无泄露 turn_plan 
PASS  回放无泄露 gold_moves 
PASS  回放无泄露 compliance_checks 

全部通过
```
