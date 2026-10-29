# 任务卡规则（每次开工先读，约 1 分钟）

项目：医药代表智能演练助手。你是接手的编码助手，**每次只做当前这一张任务卡**。本批（C 系列）是对**已上线代码**的修复，不是新建。

1. **只做当前卡**，不要预做后续卡，不要顺手重构。
2. **不得修改 `SPEC.md`、`AGENTS.md`**（`taskq.py` 会校验；被改了要 `git checkout` 恢复）。
3. **时间一律用 `datetime.now(timezone.utc)`**，不要用 `utcnow()`。ruff 与卡内代码冲突时，用最小的 `# noqa: 规则号`，并在 `docs/QUESTIONS.md` 记一行（上一批已有先例，沿用同样做法）。
4. **测试不得联网、不得调用真实模型**（用 `MockLLM`）。
5. **不替人做决定**：事实核验（`facts.yaml` 的 `verified`）、场景审核状态（`review.json`）只能由人工决定；不得改写 `facts.yaml` 的 `statement`；不得编造医学事实；任何代码、台词、提示词里**不得出现疗效或安全性的具体数字或百分比**。
6. **密钥不入库**。提交前先运行 `git status --short` 检查：**不得提交** `_tmp_*`、`Makefile` 加 6 位随机字符的临时文件、`*.egg-info`、`.env`、`data/app.db`、`data/chroma/`、`data/usage/`、`wheelhouse/`。
7. **先读后改**：本批卡要求修改**已存在**的文件。动手前先读对应文件的现有实现（里面可能有上一批为通过 lint 加的 `# noqa`、以及与参考代码不同的适配），再按卡里的“改动点”**做最小修改**，**保留原有的 `# noqa` 注释**。除非卡里写明“整体替换”，不要整文件重写。
8. **验收**：完成后运行 `python scripts/taskq.py done <卡号>`，通过才算完成。失败只看输出的**最后 40 行**；同一问题连续 3 次修不好，在 `docs/QUESTIONS.md` 记录后**停下并报告**。**不得降低或修改验收判据**来让它通过。
9. **提交与推送**（每张卡完成后）：
   `git add -A && git commit -m "[卡号] 标题" && git pull --rebase origin main && git push origin HEAD:main`
   遇到冲突或被拒：**不要强推**，停下并报告。
10. **同一时间只能有一个助手在改仓库**：开工前 `git pull --rebase origin main`；如果发现 `tasks/status.json` 里出现你没做过的卡已完成，说明另一个助手也在工作，**停下并报告**。
11. **额度将尽或需要停下**：把当前卡号、完成度、半成品文件、下一步命令、已知问题写进 `docs/HANDOFF.md`，提交并推送，再停。
12. 卡里给出的新文件“原样写入”，写完先跑测试，再按报错最小化修正；卡里没写的设计，不要自己发挥。

---

## CARD C1 | 仓库清洁 | deps: - | verify: bash scripts/check_repo_hygiene.sh

**目标**：清理被误提交或残留的临时文件，防止 `.env`、数据库、构建产物进入公开仓库。
**背景**：现状快照里出现了 `MakefileViXsHZ`、`frontend/_tmp_*`（6 个）、`backend/rep_trainer.egg-info`、本地 `.env` 与 `data/app.db`；`docs/PROGRESS.md` 里同一张卡出现了两行（说明上一批可能有两个助手同时工作过）。

**步骤**
1. 新建 `scripts/check_repo_hygiene.sh`（原样写入，`chmod +x`）：
```bash
#!/usr/bin/env bash
# 检查不该进仓库的文件是否被 git 跟踪。有问题返回 1。
cd "$(dirname "$0")/.." || exit 1
PATTERN='(^|/)(_tmp_[^/]+|Makefile[A-Za-z0-9]{6}|[^/]+\.egg-info|\.env|\.venv|node_modules|__pycache__|\.pytest_cache|\.ruff_cache)(/|$)|(^|/)data/(app\.db|chroma|usage)(/|$)|(^|/)frontend/dist(/|$)|(^|/)wheelhouse(/|$)'
bad=$(git ls-files | grep -E "$PATTERN" || true)
if [ -n "$bad" ]; then
  echo "以下文件被 git 跟踪，不应入库："
  echo "$bad" | head -40
  exit 1
fi
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
  echo "严重：.env 被跟踪，里面可能有密钥"
  exit 1
fi
echo "仓库清洁：没有发现不该入库的文件"
```
2. 运行它。**如果输出里有 `.env` 或提示“严重”**：立刻停止，不要继续，向人工报告“`.env` 被 git 跟踪，需要立即更换里面所有密钥（仓库是公开的，历史记录里也有）”。
3. 其他被跟踪的违规文件：逐个 `git rm -r --cached <路径>`。
4. `.gitignore` 追加（没有才加）：
```
_tmp_*
Makefile??????
*.egg-info/
data/app.db
data/chroma/
data/usage/
frontend/dist/
wheelhouse/
.env
```
5. 本地残留文件的删除：先运行 `diff Makefile MakefileViXsHZ`。**如果两者内容不同，先把差异报告给人工，不要删**；相同则删除。`frontend/_tmp_*` 先 `ls -la` 看内容，确认只是临时文件再删。
6. 去重文档：`awk '!seen[$0]++' docs/PROGRESS.md > /tmp/p.md && mv /tmp/p.md docs/PROGRESS.md`，`docs/QUESTIONS.md` 同样处理。
7. 在 `scripts/ci.sh` 末尾追加一行 `bash scripts/check_repo_hygiene.sh`。

**不要做**：不要用 `git filter-branch` 或改写历史。

## CARD C2 | 信号清洗守卫 | deps: - | verify: . .venv/bin/activate && pytest -q backend/tests/test_guards.py && ruff check backend

**目标**：用确定性规则兜住裁判模型的常见误判。**真实样例里**：医生只说了“我现在用得挺好的，不用换。”（不是提问），代表却被判“回避提问”并扣了信任和耐心，医生还回了一句“你没回答我的问题”，听起来很怪；同类误判在 6 场对话里至少出现 3 次。
**新建 2 个文件，内容原样写入**。

`backend/app/sessions/guards.py`
```python
"""对裁判输出做确定性清洗：模型常见的误判，用规则兜住。"""
from __future__ import annotations

import re

QUESTION_HINT = re.compile(r"[？?]|吗|呢|什么|怎么|为什么|哪|多少|能不能|是不是|有没有|行不行|可不可以")
SUPPORT = {"relevant_to_concern", "cited_evidence", "addressed_objection", "proposed_next_step",
           "asked_open_question"}
COMPLIANCE_BAITS = {"off_label_bait", "benefit_bait", "stat_bait", "promise_bait"}
# 代表对合规试探"有所回应"的信号：有这些之一，就不算回避
RESPONSES = {"declined_boundary", "accepted_benefit", "disclosed_stat", "promised_outcome",
             "off_label_claim", "exaggeration"}


def strip_event(text: str) -> str:
    """去掉医生台词开头的环境事件，如「（护士敲门递病历）」。"""
    return re.sub(r"^（[^）]*）", "", text).strip()


def norm_line(text: str) -> str:
    """台词比较用：去掉环境事件、标点和空白。"""
    return re.sub(r"[\s，。,.、；;：:！!？?（）()“”\"'‘’\-—]+", "", strip_event(text))


def has_question(text: str) -> bool:
    return bool(QUESTION_HINT.search(strip_event(text)))


def sanitize_signals(signals: list[str], last_doctor_text: str, last_bait: str | None) -> list[str]:
    sig = list(dict.fromkeys(signals))
    # 1. 医生上一句不是提问，就不可能"回避提问"
    if "ignored_doctor_question" in sig and not has_question(last_doctor_text):
        sig.remove("ignored_doctor_question")
    # 2. 已经有实质内容的回应，就不算空泛
    if "vague_or_generic" in sig and set(sig) & SUPPORT:
        sig.remove("vague_or_generic")
    # 3. 又拒绝又接受：合规上宁严勿宽，保留违规，去掉"拒绝"
    if "declined_boundary" in sig and "accepted_benefit" in sig:
        sig.remove("declined_boundary")
    # 4. 医生上一句抛了合规试探，代表既没明确拒绝、也没任何回应 → 回避边界（替代"回避提问"，避免重复扣分）
    if last_bait in COMPLIANCE_BAITS and not (set(sig) & RESPONSES):
        sig = [s for s in sig if s != "ignored_doctor_question"]
        sig.append("evaded_boundary")
    return sig
```

`backend/tests/test_guards.py`
```python
from app.sessions.guards import has_question, norm_line, sanitize_signals, strip_event


def test_has_question():
    assert has_question("你这数据哪来的？")
    assert has_question("说明书上有写吗")
    assert has_question("（护士敲门递病历）你说什么？")
    assert not has_question("我现在用得挺好的，不用换。")
    assert not has_question("三分钟，说重点。")
    assert strip_event("（接电话）嗯，你说。") == "嗯，你说。"


def test_ignored_dropped_when_doctor_did_not_ask():
    out = sanitize_signals(["ignored_doctor_question", "relevant_to_concern"], "我现在用得挺好的，不用换。", None)
    assert out == ["relevant_to_concern"]


def test_ignored_kept_when_doctor_asked():
    assert "ignored_doctor_question" in sanitize_signals(["ignored_doctor_question"], "你这药副作用不小吧？", None)


def test_vague_dropped_when_there_is_substance():
    assert sanitize_signals(["relevant_to_concern", "vague_or_generic"], "x", None) == ["relevant_to_concern"]
    assert sanitize_signals(["vague_or_generic"], "x", None) == ["vague_or_generic"]


def test_evaded_boundary_after_compliance_bait():
    assert sanitize_signals([], "最近忙，改天一起吃个饭？", "benefit_bait") == ["evaded_boundary"]
    assert sanitize_signals(["relevant_to_concern"], "你们科室会能赞助吗？", "benefit_bait") == [
        "relevant_to_concern", "evaded_boundary"]
    assert sanitize_signals(["ignored_doctor_question"], "改天一起吃个饭？", "benefit_bait") == ["evaded_boundary"]


def test_not_evaded_when_rep_responded():
    for s in ("declined_boundary", "accepted_benefit", "promised_outcome", "disclosed_stat", "off_label_claim"):
        assert "evaded_boundary" not in sanitize_signals([s], "改天一起吃个饭？", "benefit_bait")


def test_non_compliance_bait_is_never_evaded():
    assert sanitize_signals([], "你们跟司美比怎么样？", "competitor_bash_bait") == []
    assert sanitize_signals([], "能保证有效吗？", "exaggeration_bait") == []
    assert sanitize_signals([], "你好", None) == []


def test_declined_and_accepted_keeps_the_violation():
    out = sanitize_signals(["declined_boundary", "accepted_benefit"], "改天吃个饭？", "benefit_bait")
    assert out == ["accepted_benefit"]


def test_norm_line_ignores_events_and_punctuation():
    assert norm_line("（接电话）三分钟，说重点。") == norm_line("三分钟说重点") == "三分钟说重点"
```

**不要做**：本卡不接入引擎（C5 再接）。

## CARD C3 | 医生意图选择器 v2 | deps: - | verify: . .venv/bin/activate && pytest -q backend/tests/test_intent.py && ruff check backend

**目标**：修复三个自然度问题：① 代表提出了下一步，医生却去问竞品（陷阱抢在回应之前）；② 收尾只有一句固定台词，每场都说“今天先到这儿吧，我还有病人”；③ “重复问题”台词没有指代内容（“我刚才问的是这个”）。并新增两个意图：认可对方守规矩、追问没回答的试探。
**整体替换这两个文件**（内容原样写入）：

`backend/app/sessions/intent.py`
```python
"""医生"这一句要做什么"由规则决定（确定性），模型只负责把它说得像人。
这样小模型也不容易跑偏，也不会说成客服腔。"""
from __future__ import annotations

import random
import re

from ..corpus.loader import SceneBank
from ..corpus.maps import BAIT_INTENT, SKELETON_END
from ..models import DoctorState

CLOSING_INTENT = {
    "doctor_left": "close_hard",
    "agreed_next_step": "close_followup",
    "materials_left": "close_materials",
    "referred": "close_refer",
    "soft_decline": "close_soft",
    "time_up": "close_soft",
}
POSITIVE = {"relevant_to_concern", "asked_open_question", "empathy_shown", "addressed_objection", "cited_evidence",
            "declined_boundary"}
NEGATIVE_ORDER = [
    ("off_label_claim", "push_back_label"), ("exaggeration", "push_back_evidence"),
    ("competitor_bashing", "push_back_tone"), ("accepted_benefit", "pull_back"),
    ("disclosed_stat", "pull_back"), ("promised_outcome", "pull_back"), ("evaded_boundary", "press_again"),
    ("pushy", "cool_down"),
    ("ignored_doctor_question", "repeat_question"), ("vague_or_generic", "ask_specific"),
]

# 意图 -> (中文名, 给模型的指令, 台词库类别（可为 None）, 内置口吻示例)。示例只学说话方式，不是事实。
INTENTS: dict[str, tuple[str, str, str | None, list[str]]] = {
    "open_up": ("愿意多说一点", "用一个具体的个案或日常门诊的感受，多说一句自己的情况，不要总结", None,
                ["我们科上个月有个病人，用了同类药一直恶心。", "这类患者我门诊挺多的，就是不好管。", "说起来，上次有个患者就是这样。"]),
    "reveal_case": ("流露真实顾虑", "用自己的话、用一个个案，流露你心里真正的顾虑，只透露一部分，不要照搬原句", None,
                    ["不瞒你说，我担心的倒不是这个。", "我们科之前有个病人，就是吃着吃着自己停了。", "我其实更在意患者能不能坚持。"]),
    "probe_evidence": ("追问出处", "追问研究出处、入组人群或对照组，只问一个点", None,
                       ["这个研究是哪篇？入组的是什么人？", "对照组用的是什么药？", "你说的结果，随访多久？"]),
    "hedge_next": ("含糊地接下一步", "对代表提出的下一步给一个有保留、有条件的回应，不要轻易答应", None,
                   ["下周看吧，我这周排满了。", "可以，你先把资料发我看看。", "行，到时候再约。"]),
    "ask_specific": ("要求说具体", "嫌对方说得空，要求说具体、说重点，一句话", None,
                     ["具体说，对我这类患者有什么用？", "别说虚的，一句话说清楚。", "你直接说重点。"]),
    "repeat_question": ("重复自己的问题", "把你刚才的问题用一句话重新问一遍，要说出问题的具体内容，不要用“这个”“那个”指代", None,
                        ["我问的是数据出处，你还没答。", "刚才问的是副作用，你先答这一点。", "你没答我的问题，我问的是适用人群。"]),
    "accept_boundary": ("认可对方守规矩", "对方明确拒绝了不合规的试探，你表示理解并回到正题，语气缓和", None,
                        ["行，那就按规矩来。", "也对，我就随口一说。", "好，那聊正事吧。"]),
    "press_again": ("追问没回答的试探", "对方没有正面回答你刚才的试探，换个说法再问一次，语气稍重", None,
                    ["你别岔开，直接说行不行？", "我问的你还没答，给个准话。", "这事你能不能办？"]),
    "cool_down": ("不舒服，收紧话题", "表示被催促不舒服，语气收紧", None,
                  ["你别催我，我还没想好。", "这事不是今天能定的。", "你先别急。"]),
    "push_back_label": ("质疑是否超说明书", "质疑这个说法是否在说明书适应症内，追问依据", None,
                        ["说明书上有写这个人群吗？", "这个适应症批了吗？", "这个说法有依据吗？"]),
    "push_back_evidence": ("质疑数据与说法", "对夸大或绝对化的说法表示不信任，追问出处", None,
                           ["这数据哪来的？", "你说得太满了吧。", "出处呢？别光说结论。"]),
    "push_back_tone": ("对贬低竞品反感", "对贬低别的药表示反感，让对方说自己的", None,
                       ["你别踩别人，说你们自己的。", "那个药我也用过，没你说的那么差。", "说你们的就行。"]),
    "pull_back": ("退一步，守边界", "对不合规的话或试探收口，表示按规定来，语气克制", None,
                  ["这个就别提了，按规定来。", "你这样说，我不方便继续了。", "这些事我们不聊。"]),
    "time_pressure": ("催着说重点", "表现出时间紧，催代表说重点或被打断", "pressure_and_interrupt",
                      ["三分钟，说重点。", "你直接说，对我们科有什么用。"]),
    "hard_refuse": ("硬拒绝", "直接、简短地拒绝，不留余地但不失礼", "hard_refusal",
                    ["我现在用得挺好的，不用换。"]),
    "soft_refuse": ("温柔拒绝", "用听起来客气、实则告别的话收场，不要明确说不", "soft_refusal",
                    ["你讲得挺好的，有机会再合作。"]),
    "neutral_ack": ("简短回应", "简短回应，让对方继续", None, ["嗯，你接着说。", "行，我听着。"]),
    "bait_off_label": ("试探适应症边界", "自然地试探：问这个药能不能用于尚未确认的适应症或人群，不要点破你在试探", None,
                       ["那脂肪肝的患者能用吗？", "别的人群也能用吧？", "说明书外的情况呢？"]),
    "bait_competitor": ("引导评价竞品", "抛出一个竞品话题，引导代表评价或比较", None,
                        ["你们这个跟司美比怎么样？", "人家那个药是不是不行？", "同类的你怎么看？"]),
    "bait_exaggeration": ("引诱夸大", "问一个绝对化的问题，引诱代表夸大", None,
                          ["能保证有效吗？", "是不是比别的药都好？", "有没有副作用？别骗我。"]),
    "bait_benefit": ("试探利益", "半开玩笑地试探：吃饭、赞助等好处，语气随意", None,
                     ["最近忙，改天一起吃个饭？", "你们科室会能不能赞助点别的？", "你们能给点什么支持？"]),
    "bait_stat": ("试探统方", "半开玩笑地问代表能不能看到或说说科室的用药量", None,
                  ["你给我说说，我们科这个月开了多少你们的药？", "你们那边应该能查到吧？"]),
    "bait_promise": ("试探承诺", "试探代表会不会承诺销售结果或额外支持", None,
                     ["我用了，你们能保证什么？", "别光说学术，实在点。"]),
    "close_followup": ("同意下一步并收尾", "认可对方提出的下一步，简短确认时间", "closing:followup_set",
                       ["行，下周二门诊结束后你来一趟。", "可以，你周四下午来，我在科里。", "那就约下周，我让护士给你留个时间。"]),
    "close_materials": ("留下资料收尾", "简短收尾，让对方把资料留下", "closing:materials_left",
                        ["资料先放这儿吧。", "放这儿，我有空翻翻。", "留下吧，回头我看看。"]),
    "close_refer": ("转介收尾", "把对方转给科室里管这块的人", "closing:referred",
                    ["你先跟我们科管这块的大夫对接一下。", "这块是我们科另一位大夫在管，你找他聊。"]),
    "close_soft": ("客气地结束", "客气地结束，不做任何承诺", "closing:soft_decline",
                   ["好的，我知道了，有需要再联系你。", "行，今天就这样吧，谢谢你来。", "嗯，我了解了，你先忙。"]),
    "close_hard": ("明确结束", "表示还有病人，明确结束这次谈话", "closing:hard_decline",
                   ["今天先到这儿吧，我还有病人。", "不好意思，下一位病人在等了。", "就到这儿吧，我得去查房了。"]),
}


def resolve_end(end: str | None, state: DoctorState, skeleton_id: str | None) -> str | None:
    """把引擎的 time_up 换成更真实的结局；其他结局原样返回。"""
    if end != "time_up":
        return end
    if skeleton_id in SKELETON_END:
        return SKELETON_END[skeleton_id]
    return "materials_left" if state.trust >= 65 else "soft_decline"


def choose_intent(*, end: str | None, bait: str | None, reveal: bool, signals: list[str], state: DoctorState,
                  rep_turn_no: int, style: str, last_intent: str | None) -> str:
    sig = set(signals)
    if end:
        return CLOSING_INTENT[end]
    if bait:
        return BAIT_INTENT[bait]
    if reveal:
        return "reveal_case"
    for s, intent in NEGATIVE_ORDER:
        if s in sig:
            return intent
    if "declined_boundary" in sig:
        return "accept_boundary"
    if "proposed_next_step" in sig:
        return "hedge_next"
    if (state.patience < 30 or style == "busy_efficient") and last_intent != "time_pressure":
        return "time_pressure"
    if not (sig & POSITIVE):
        if rep_turn_no <= 2:
            return "hard_refuse" if state.trust < 35 else "soft_refuse"
        return "ask_specific"
    if "cited_evidence" in sig:
        return "probe_evidence"
    return "open_up"


def _bank_lines(bank: SceneBank, category: str | None) -> list[str]:
    if not category:
        return []
    if category.startswith("closing:"):
        return bank.closing(category.split(":", 1)[1])
    return bank.lines(category)


def _key(text: str) -> str:
    return re.sub(r"[\s，。,.、；;：:！!？?（）()“”\"'‘’\-—]+", "", text)


def pick_examples(bank: SceneBank, intent: str, k: int = 3, seed: str = "",
                  avoid: tuple[str, ...] | list[str] = ()) -> list[str]:
    """取口吻示例。avoid 是最近说过的医生台词：优先避开它们；全被避开时才退回完整池。"""
    _, _, category, builtin = INTENTS[intent]
    pool = list(dict.fromkeys(_bank_lines(bank, category) + builtin))
    skip = {_key(a) for a in avoid}
    fresh = [x for x in pool if _key(x) not in skip]
    pool = fresh or pool
    random.Random(f"{seed}:{intent}").shuffle(pool)
    return pool[:k]


def fallback_line(bank: SceneBank, intent: str, seed: str = "",
                  avoid: tuple[str, ...] | list[str] = ()) -> str:
    """模型输出不合格时的兜底：直接取台词库里的一句（确定性、一定自然，且尽量不重复刚说过的话）。"""
    return pick_examples(bank, intent, 1, seed, avoid)[0]
```

`backend/tests/test_intent.py`
```python
import pytest

from app.corpus import load_bank
from app.models import DoctorState
from app.sessions.intent import INTENTS, choose_intent, fallback_line, pick_examples, resolve_end

BANK = load_bank()


def ci(**kw):
    base = dict(end=None, bait=None, reveal=False, signals=[], state=DoctorState(trust=50, patience=60, engagement=50),  # noqa: C408
                rep_turn_no=3, style="friendly_open", last_intent=None)
    base.update(kw)
    return choose_intent(**base)


def test_resolve_end():
    hi, lo = DoctorState(trust=70), DoctorState(trust=50)
    assert resolve_end("time_up", hi, None) == "materials_left"
    assert resolve_end("time_up", lo, None) == "soft_decline"
    assert resolve_end("time_up", hi, "S06") == "referred"
    assert resolve_end("time_up", hi, "S07") == "soft_decline"
    assert resolve_end("doctor_left", hi, "S06") == "doctor_left"
    assert resolve_end(None, hi, None) is None


def test_boundary_intents():
    assert ci(signals=["declined_boundary"]) == "accept_boundary"
    assert ci(signals=["evaded_boundary"]) == "press_again"
    assert ci(signals=["declined_boundary", "proposed_next_step"]) == "accept_boundary"
    assert ci(signals=["accepted_benefit", "declined_boundary"]) == "pull_back"
    assert ci(bait="stat_bait", signals=["evaded_boundary"]) == "bait_stat"


def test_avoid_recent_lines_and_variety():
    for intent in ("close_hard", "close_soft", "close_followup", "close_materials"):
        assert len(pick_examples(BANK, intent, 99, "s")) >= 3
    full = pick_examples(BANK, "close_hard", 99, "s")
    got = fallback_line(BANK, "close_hard", "s", avoid=[full[0], full[1]])
    assert got not in full[:2]
    assert fallback_line(BANK, "close_hard", "s", avoid=full) in full            # 全避开时退回完整池，不崩


def test_repeat_question_examples_name_the_question():
    for e in pick_examples(BANK, "repeat_question", 99, "s"):
        assert "这个" not in e and "那个" not in e


def test_closing_intents():
    assert ci(end="doctor_left") == "close_hard" and ci(end="agreed_next_step") == "close_followup"
    assert ci(end="materials_left") == "close_materials" and ci(end="referred") == "close_refer"
    assert ci(end="soft_decline") == "close_soft"


def test_priority_order():
    assert ci(bait="off_label_bait") == "bait_off_label"
    assert ci(bait="benefit_bait", signals=["exaggeration"]) == "bait_benefit"
    assert ci(reveal=True, signals=["pushy"]) == "reveal_case"
    assert ci(signals=["off_label_claim", "cited_evidence"]) == "push_back_label"
    assert ci(signals=["exaggeration"]) == "push_back_evidence"
    assert ci(signals=["competitor_bashing"]) == "push_back_tone"
    for s in ("accepted_benefit", "disclosed_stat", "promised_outcome"):
        assert ci(signals=[s]) == "pull_back"
    assert ci(signals=["pushy"]) == "cool_down"
    assert ci(signals=["ignored_doctor_question"]) == "repeat_question"
    assert ci(signals=["vague_or_generic"]) == "ask_specific"


def test_normal_flow():
    assert ci(style="busy_efficient", signals=["asked_open_question"]) == "time_pressure"
    assert ci(style="busy_efficient", signals=["proposed_next_step"]) == "hedge_next"     # 先回应对方提出的下一步
    assert ci(state=DoctorState(trust=50, patience=10), signals=["proposed_next_step"]) == "hedge_next"
    assert ci(style="busy_efficient", signals=["asked_open_question"], last_intent="time_pressure") == "open_up"
    assert ci(signals=[], rep_turn_no=1, state=DoctorState(trust=20, patience=60)) == "hard_refuse"
    assert ci(signals=[], rep_turn_no=1) == "soft_refuse"
    assert ci(signals=[], rep_turn_no=4) == "ask_specific"
    assert ci(signals=["cited_evidence"]) == "probe_evidence"
    assert ci(signals=["proposed_next_step", "relevant_to_concern"]) == "hedge_next"
    assert ci(signals=["asked_open_question"]) == "open_up"
    assert ci(state=DoctorState(trust=50, patience=20), signals=["asked_open_question"]) == "time_pressure"


@pytest.mark.parametrize("intent", sorted(INTENTS))
def test_every_intent_has_examples_and_short_lines(intent):
    cn, directive, _, _ = INTENTS[intent]
    assert cn and directive
    ex = pick_examples(BANK, intent, 3, seed="s1")
    assert ex and len(set(ex)) == len(ex)
    assert fallback_line(BANK, intent, "s1") in pick_examples(BANK, intent, 99, seed="s1")
    assert all("%" not in e for e in ex)


def test_examples_are_deterministic_and_use_bank():
    assert pick_examples(BANK, "soft_refuse", 3, "a") == pick_examples(BANK, "soft_refuse", 3, "a")
    assert all(x in BANK.lines("soft_refusal") for x in pick_examples(BANK, "soft_refuse", 3, "a"))
    pool = pick_examples(BANK, "close_followup", 99, "z")
    assert fallback_line(BANK, "close_followup", "z") in pool
    assert BANK.closing("followup_set")[0] in pool                      # 台词库里的句子仍在池中
```

**不要做**：不要改动 `INTENTS` 里的示例台词；本卡不接入引擎。

## CARD C4 | 合规信号全链路 | deps: - | verify: . .venv/bin/activate && pytest -q backend/tests/test_state.py backend/tests/test_models.py backend/tests/test_prompt_v2.py && ruff check backend && cd frontend && pnpm exec tsc --noEmit && pnpm exec vitest run

**目标**：补上“代表明确拒绝了不合规试探”（`declined_boundary`，好）和“代表回避了试探”（`evaded_boundary`，不好）两个信号。**真实样例里**：S12 的好代表对“吃个饭”“赞助点别的”全程没有正面回应，系统却判它合规并让医生同意了下一步——**不回应不等于拒绝**。

**改动点（逐项做）**
1. `backend/app/models/constants.py`：`SIGNALS` 追加 `"declined_boundary", "evaded_boundary"`。
2. `backend/app/models/domain.py`：`Signal` 的 Literal 同步追加这两个。
3. `data/rubric/state_rules.yaml`：`deltas` 追加 `declined_boundary: {trust: 8, patience: 3}`、`evaded_boundary: {trust: -6, patience: -6}`；`negative_signals` 追加 `evaded_boundary`。
4. `backend/app/sessions/rules.py`：`DEFAULT_DELTAS` 与 `negative_signals` 的默认值同步（现有测试会比对 yaml 与默认值，必须一致）。
5. `prompts/signal_judge.md`：版本改为 `0.3.0`；在“可选信号及含义”末尾追加：
```
- declined_boundary：对医生关于饭局、赞助、礼品、处方量、销售承诺或范围外用法的试探，明确而友好地拒绝，并说明按规定办或转回学术交流
```
   并在“判定原则”末尾追加一条：`evaded_boundary 由程序判定，你不要输出它。` `prompts/CHANGELOG.md` 追加一行。
6. 测试：`backend/tests/test_prompt_v2.py` 的 `test_judge_has_compliance_signals` 里的信号列表追加 `"declined_boundary"`；`backend/tests/test_state.py` 追加：
```python
def test_boundary_signal_rules():
    assert R.deltas["declined_boundary"]["trust"] > 0 and R.deltas["evaded_boundary"]["trust"] < 0
    assert "evaded_boundary" in R.negative_signals
```
7. 前端：`frontend/src/types.ts` 的 `SIGNALS` 追加这两个；`frontend/src/labels.ts`：`SIGNAL_LABEL` 追加 `declined_boundary: "明确守住边界"`、`evaded_boundary: "回避了边界问题"`；`SIGNAL_POLARITY` 前者 `"good"`，后者 `"bad"`。（`lib.test.ts` 里“每个信号都有标签”的测试会自动检查。）

## CARD C5 | 引擎接入：清洗、陷阱归属、防重复 | deps: C2, C3, C4 | verify: . .venv/bin/activate && pytest -q backend/tests/test_engine.py backend/tests/test_intent.py backend/tests/test_guards.py backend/tests/test_state.py && ruff check backend

**目标**：把守卫和新意图接进引擎，并修三个引擎问题（均来自真实样例）：
- **陷阱串场**：S04（硬拒绝）里医生莫名问“你们这药跟司美比怎么样”“其他情况能用吗”，原因是场景没有陷阱时回退用了**画像自带的陷阱**。骨架场景的陷阱必须只由场景决定。
- **不回应下一步**：代表刚提出下一步，医生却去抛陷阱。
- **台词重复**：同一场里医生说了两句一模一样的话。

**改动点（在 `backend/app/sessions/engine.py`）**
1. 导入：`from .guards import norm_line, sanitize_signals, strip_event`。
2. **用下面的版本替换 `step()`、`_check_reply()`、`_reply()`**（保留文件里原有的其他方法与 `# noqa` 注释；这三个方法是类方法，注意缩进）：
```python
    def step(self, session, scenario, persona, rep_text) -> StepResult:
        rep_text = rep_text.strip()
        rep_turn_no = sum(t.speaker == "rep" for t in session.turns) + 1
        prev_state = next((t.state_after for t in reversed(session.turns) if t.state_after), initial_state(persona))
        history = format_history(session.turns)
        facts = self._retrieve(rep_text, persona)
        metas = [t.meta for t in session.turns if t.speaker == "doctor"]
        last_doc_text = next((t.text for t in reversed(session.turns) if t.speaker == "doctor"), "")
        last_bait = metas[-1].get("bait") if metas else None
        recent = [strip_event(t.text) for t in session.turns if t.speaker == "doctor"][-3:]

        signals, j_deg = self._judge(scenario, persona, history, rep_text, facts + self._indication_facts())
        signals = sanitize_signals(signals, last_doc_text, last_bait)
        state = apply_signals(prev_state, signals, self.rules, natural_decay(persona))
        end = resolve_end(decide_end(state, signals, rep_turn_no, persona.time_budget_turns, self.rules),
                          state, scenario.skeleton_id)
        reveal = end is None and should_reveal(state, signals, self.rules)
        if reveal:
            state.revealed_hidden_objection = True
        # 骨架场景的陷阱只由场景决定；旧场景（无 skeleton_id）才回退到画像陷阱
        baits = scenario.baits if scenario.skeleton_id else [t for t in persona.traps if t != "none"]
        calm = {"proposed_next_step", "declined_boundary", "evaded_boundary"} & set(signals)
        bait = None if (reveal or end or calm) else next_bait(baits, metas, rep_turn_no, self.rules)
        last_intent = metas[-1].get("intent") if metas else None
        intent = choose_intent(end=end, bait=bait, reveal=reveal, signals=signals, state=state,
                               rep_turn_no=rep_turn_no, style=persona.style, last_intent=last_intent)
        event = self._event(scenario, rep_turn_no, end)
        reply, r_deg = self._reply(scenario, persona, state, history, rep_text, facts, intent,
                                   f"{session.id}:{rep_turn_no}", recent)
        text = f"（{event}）{reply}" if event else reply

        session.turns.append(Turn(idx=len(session.turns), speaker="rep", text=rep_text, signals=signals,
                                  state_after=state))
        session.turns.append(Turn(idx=len(session.turns), speaker="doctor", text=text, state_after=state,
                                  meta={"rep_turn_no": rep_turn_no, "bait": bait, "revealed": reveal,
                                        "intent": intent, "event": event, "end_hint": end,
                                        "degraded": j_deg or r_deg}))
        if end:
            session.ended_at = datetime.now(timezone.utc)  # noqa: UP017
            session.end_reason = end
        return StepResult(text, state, signals, end is not None, end, j_deg or r_deg)

    def _check_reply(self, persona, reply, intent, corpus, avoid) -> str | None:
        if len(reply.strip()) > 60:
            return "太长，医生一般只说一两句短话"
        if any(w in reply for w in BAD_WORDS):
            return "出现了不该出现的字眼"
        if norm_line(reply) in {norm_line(a) for a in avoid}:
            return "和刚说过的话重复了，换一种说法"
        if intent != "reveal_case" and leaks_hidden(persona.hidden_objection, reply):
            return "直接说出了隐藏的顾虑"
        if unsupported_numbers(reply, corpus):
            return "出现了资料和对话中不存在的数字"
        return None

    def _reply(self, scenario, persona, state, history, rep_text, facts, intent, seed, avoid=()) -> tuple[str, bool]:
        prompt = load_prompt("doctor_reply")
        cn, directive, _, _ = INTENTS[intent]
        examples = "\n".join("- " + e for e in pick_examples(self.bank, intent, 3, seed, avoid))
        corpus = rep_text + format_facts(facts) + history
        note = ""
        for _ in range(2):
            user = prompt.render(
                department_cn=DEPT_CN[persona.department], title=persona.title, hospital_tier=persona.hospital_tier,
                style_desc=STYLE_DESC[persona.style], speech_habits=persona.speech_habits,
                current_habit=persona.current_habit, hidden_objection=persona.hidden_objection,
                setting_cn=setting_cn(scenario.setting), history=history, rep_text=safe_text(rep_text),
                intent_cn=cn, intent_directive=directive, tone_hint=tone_hint(state), examples=examples,
                facts=format_facts(facts), retry_note=note)
            out, degraded = structured_call(
                self.provider, prompt_name="doctor_reply", system="你是严格输出 JSON 的角色扮演助手。",
                messages=[{"role": "user", "content": user}], model_cls=DoctorReply,
                fallback=DoctorReply(reply=fallback_line(self.bank, intent, seed, avoid)),
                max_retries=1, temperature=0.8)
            if degraded:
                return out.reply, True
            reason = self._check_reply(persona, out.reply, intent, corpus, avoid)
            if reason is None:
                return out.reply.strip(), False
            note = f"【上一次不合格：{reason}。请重写并避免该问题。】"
        return fallback_line(self.bank, intent, seed, avoid), True
```
   若文件里原来的 `session.ended_at` 那行已有 `# noqa: UP017`，保持一致即可。
3. `intent.py` 已在 C3 提供 `avoid` 参数；本卡不要再改它。

**测试改动（`backend/tests/test_engine.py`，只追加）**：
```python
def test_ignored_flag_dropped_when_doctor_made_a_statement():
    engine, _, persona, scenario, sess = setup(judge=J("ignored_doctor_question"))
    engine.step(sess, scenario, persona, "主任您好，想先了解一下您门诊的情况。")
    assert sess.turns[1].signals == []                       # 开场白“我只有几分钟，你说吧。”不是提问


def test_skeleton_scenario_never_uses_persona_traps():
    engine, _, persona, scenario, sess = setup(base=6, scenario_kw={"skeleton_id": "S04", "baits": []})
    for i in range(4):
        engine.step(sess, scenario, persona, f"第{i}句")
    assert all(t.meta.get("bait") is None for t in sess.turns if t.speaker == "doctor")


def test_next_step_proposal_suppresses_bait():
    engine, _, persona, scenario, sess = setup(judge=J("proposed_next_step"), scenario_kw={
        "skeleton_id": "S12", "baits": ["benefit_bait"]})
    for i in range(3):
        engine.step(sess, scenario, persona, f"下周约您聊聊，第{i}次")
    assert all(t.meta.get("bait") is None for t in sess.turns if t.speaker == "doctor")
    assert sess.turns[-1].meta["intent"] in ("hedge_next", "close_followup", "close_materials", "close_soft")


def test_evading_a_compliance_probe_is_flagged_and_pressed():
    engine, mock, persona, scenario, sess = setup(base=0, scenario_kw={"skeleton_id": "S12", "baits": ["benefit_bait"]})
    engine.step(sess, scenario, persona, "您好")                       # 第 1 回合
    engine.step(sess, scenario, persona, "我先给您介绍下资料")           # 第 2 回合：医生抛出饭局试探
    assert sess.turns[-1].meta["bait"] == "benefit_bait"
    res = engine.step(sess, scenario, persona, "资料第三页是研究摘要")    # 没回应试探
    assert "evaded_boundary" in res.signals and sess.turns[-1].meta["intent"] == "press_again"


def test_declining_a_compliance_probe_is_accepted():
    engine, mock, persona, scenario, sess = setup(base=0, scenario_kw={"skeleton_id": "S12", "baits": ["benefit_bait"]})
    engine.step(sess, scenario, persona, "您好")
    engine.step(sess, scenario, persona, "我先给您介绍下资料")
    mock.set("signal_judge", J("declined_boundary"))
    res = engine.step(sess, scenario, persona, "吃饭这个我得婉拒，公司有规定，学术问题随时聊。")
    assert "declined_boundary" in res.signals and sess.turns[-1].meta["intent"] == "accept_boundary"


def test_doctor_never_repeats_a_line_even_if_model_does():
    engine, mock, persona, scenario, sess = setup(reply=D("嗯，你接着说。"))
    for i in range(4):
        engine.step(sess, scenario, persona, f"第{i}句话")
    lines = [t.text for t in sess.turns if t.speaker == "doctor"]
    assert len(set(lines)) == len(lines)
```
（`setup()`、`J()`、`D()` 沿用该测试文件已有的辅助函数。若 `base=0` 的画像因难度而在第 2 回合前结束，把 `base` 换成同科室的其他画像或调大 `time_budget_turns`，**不要改断言**。）

## CARD C6 | 称呼与职称一致，并重新生成场景 | deps: - | verify: . .venv/bin/activate && pytest -q backend/tests/test_skeleton_gen.py && python scripts/verify_scenarios_v2.py

**目标**：修复场景文字里“主任”硬编码的问题。**真实样例里**：对主治医师（二级医院）的场景写着“第一次拜访该科主任”，与职称矛盾。
**前置检查**：先看 `data/scenarios/review.json`。**如果里面已经有人工审核结果（非空），停止并报告**，不要重新生成（会让审核编号对不上）。

**改动点（`backend/app/scenarios/skeleton_gen.py`，保留已有的 `# noqa`）**
1. 新增两个函数，放在 `check_fill` 之前：
```python
def honorific(p: DoctorPersona) -> str:
    """称呼要与职称一致：主任医师、副主任医师可称主任，主治医师只能称医生。"""
    return "主任" if "主任" in p.title else "医生"


def localize(text: str, p: DoctorPersona) -> str:
    h = honorific(p)
    return text if h == "主任" else text.replace("主任", h)
```
2. `check_fill` 开头（`text = ...` 之后）加：
```python
    if honorific(p) != "主任" and "主任" in text:
        return "称呼与职称不符（主治医师不应称主任）"
```
3. `fallback_fill` 改成：
```python
    pre = localize(sk.rep_pre_info, p)
    brief = f"您将拜访{DEPT_CN[p.department]}的{p.title}（{p.hospital_tier}）。{pre}"
    return FillDraft(context_brief=brief[:160], pre_info=pre[:120])
```
4. `fill_one` 渲染提示词时：`rep_goal=localize(sk.rep_goal, p)`、`rep_pre_info=localize(sk.rep_pre_info, p)`。
5. `build_scenarios` 构造 `Scenario` 时：`rep_goal=localize(sk.rep_goal, p)`，`success_criteria=[localize(c, p) for c in sk.success_criteria]`。
6. `prompts/scenario_fill.md`：“要求”末尾追加第 4 条：`4. 称呼必须与职称一致：这位医生的职称是“{{title}}”，主治医师不得称为“主任”，请统一称“医生”。`（变量沿用已有的 `title`；版本改 `0.2.0`；`CHANGELOG.md` 记一行。）
7. `scripts/verify_scenarios_v2.py` 的循环里追加：
```python
        if "主任" not in p.title and any("主任" in x for x in (r.rep_goal, r.context_brief, r.pre_info, *r.success_criteria)):
            errs.append(f"{r.id} 称呼与职称不符")
```
8. 测试追加到 `backend/tests/test_skeleton_gen.py`：
```python
def test_titles_are_consistent_in_public_texts(tmp_path):
    zhuzhi = [p.model_copy(update={"title": "主治医师"}) for p in DEMO]
    build_scenarios(None, zhuzhi, BANK, out_dir=tmp_path)
    rows = [json.loads(x) for x in (tmp_path / "scenarios.jsonl").read_text(encoding="utf-8").splitlines()]
    for r in rows:
        for f in ("rep_goal", "context_brief", "pre_info"):
            assert "主任" not in r[f], (r["id"], f)
        assert all("主任" not in c for c in r["success_criteria"])


def test_check_fill_rejects_wrong_honorific():
    p = DEMO[0].model_copy(update={"title": "主治医师"})
    bad = FillDraft(context_brief="您将拜访一位内分泌科的主治医师，这次第一次拜访该科主任，时间很紧。",
                    pre_info="上次见面气氛一般，没有细聊。")
    assert "称呼" in check_fill(p, bad)
```
9. 重新生成并入库：沿用 `scripts/run_real_gen.sh` 里连接 sutai Ollama 的方式运行 `python scripts/gen_scenarios_v2.py`，再 `python scripts/seed.py`、`make review`。把 `docs/SCENARIO_REPORT.md` 里 `via` 的 `fallback` 数量写进汇报；若 fallback 的场景集中在某个科室，去看日志找原因。

**不要做**：不要创建或修改 `review.json`。

## CARD C7 | 对话质量指标与自适应代表模拟器 | deps: C5, C6 | verify: . .venv/bin/activate && pytest -q backend/tests/test_metrics.py && ruff check backend && python scripts/sim_session.py

**目标**：把“好代表信任度高于差代表”这种弱判据，换成能抓住上述问题的**自动检查**。**真实样例里**的模拟代表是固定脚本，不看医生说了什么，所以“好代表”其实一直在答非所问；本卡用模型扮演会回应医生的代表，并检查：误判为“回避提问”的数量、医生重复台词的数量、平均字数、兜底率，以及 S12 里好代表是否真的被识别为“明确拒绝”、差代表是否真的触发了合规违规信号。
**新建/整体替换这些文件（原样写入）**：

`backend/app/sessions/metrics.py`
```python
"""对话质量的可自动检查指标（用于冒烟和回归）。传入的 turns 需有 speaker/text/signals/meta 属性。"""
from __future__ import annotations

import re

from .guards import has_question, strip_event


def _norm(s: str) -> str:
    return re.sub(r"[\s，。,.、；;：:！!？?（）()“”\"'‘’\-—]+", "", strip_event(s))


def doctor_lines(turns) -> list[str]:
    return [strip_event(t.text) for t in turns if t.speaker == "doctor"]


def count_false_ignored(turns) -> int:
    """代表被标"回避提问"，但医生上一句其实不是提问。清洗之后这个数必须是 0。"""
    n = 0
    for i, t in enumerate(turns):
        if i > 0 and t.speaker == "rep" and "ignored_doctor_question" in t.signals and not has_question(turns[i - 1].text):
            n += 1
    return n


def count_repeats(turns) -> int:
    """同一场里医生说了重复的话（含开场白）。必须是 0。"""
    seen: set[str] = set()
    n = 0
    for t in turns:
        if t.speaker == "doctor":
            k = _norm(t.text)
            n += k in seen
            seen.add(k)
    return n


def avg_doctor_len(turns) -> float:
    lines = [x for x in doctor_lines(turns)]
    return sum(len(x) for x in lines) / len(lines) if lines else 0.0


def fallback_rate(turns) -> float:
    docs = [t for t in turns if t.speaker == "doctor" and t.meta.get("rep_turn_no", 0) > 0]
    return sum(1 for t in docs if t.meta.get("degraded")) / len(docs) if docs else 0.0


def signals_seen(turns) -> set[str]:
    return {s for t in turns if t.speaker == "rep" for s in t.signals}
```

`backend/tests/test_metrics.py`
```python
from types import SimpleNamespace as NS

from app.sessions.metrics import (avg_doctor_len, count_false_ignored, count_repeats, fallback_rate,
                                  signals_seen)


def T(speaker, text, signals=(), meta=None):
    return NS(speaker=speaker, text=text, signals=list(signals), meta=meta or {})


def test_false_ignored_counts_only_when_doctor_did_not_ask():
    turns = [T("doctor", "我现在用得挺好的，不用换。"), T("rep", "您好", ["ignored_doctor_question"]),
             T("doctor", "你这数据哪来的？"), T("rep", "稍后给您", ["ignored_doctor_question"])]
    assert count_false_ignored(turns) == 1


def test_repeats_ignore_punctuation_and_events():
    turns = [T("doctor", "三分钟，说重点。"), T("rep", "x"), T("doctor", "（接电话）三分钟说重点"), T("doctor", "嗯。")]
    assert count_repeats(turns) == 1


def test_length_fallback_and_signals():
    turns = [T("doctor", "一二三四五", meta={"rep_turn_no": 0}), T("rep", "x", ["cited_evidence"]),
             T("doctor", "一二三", meta={"rep_turn_no": 1, "degraded": True}),
             T("doctor", "一二三四五六七", meta={"rep_turn_no": 2, "degraded": False})]
    assert avg_doctor_len(turns) == 5.0
    assert fallback_rate(turns) == 0.5
    assert signals_seen(turns) == {"cited_evidence"}
    assert avg_doctor_len([]) == 0.0 and fallback_rate([]) == 0.0
```

`prompts/rep_bot.md`
```markdown
---
version: 0.1.0
---
你在扮演一位医药代表，用来测试一个拜访演练系统。你的水平和风格如下：
{{level_desc}}

## 场景
- 你本次的目标：{{rep_goal}}
- 背景：{{context_brief}}
- 前情：{{pre_info}}

## 对话（最近几轮）
{{history}}

## 要求
1. 只说 1~2 句话，每句不超过 40 字，口语化。
2. 必须回应医生的上一句话，不要自说自话，不要重复自己说过的话。
3. 不要编造任何疗效、安全性的具体数字。
4. 只写代表要说的话，不要写动作描写。

## 输出格式
只输出 JSON：{"say": "代表的话"}
```

`scripts/sim_session.py`（整体替换旧脚本）
```python
"""自适应代表模拟器：用模型扮演"好代表/差代表"，与对话引擎真实对练，输出样例对话与质量指标。
用法：python scripts/sim_session.py     （需要真实模型；mock 下直接退出）"""
import sys
import time
from pathlib import Path

sys.path.insert(0, "backend")
from pydantic import BaseModel, Field  # noqa: E402

from app.llm import get_provider, get_tracker, load_prompt, structured_call  # noqa: E402
from app.models import DoctorPersona, Scenario  # noqa: E402
from app.rag import KnowledgeBase  # noqa: E402
from app.scenarios.review import load_review, usable  # noqa: E402
from app.sessions import SessionEngine  # noqa: E402
from app.sessions.engine import format_history  # noqa: E402
from app.sessions.metrics import (avg_doctor_len, count_false_ignored, count_repeats, fallback_rate,  # noqa: E402
                                  signals_seen)

LEVELS = {
    "good": ("水平较好：先认同医生再提问；只说有出处的信息，不夸大、不贬低竞品；医生试探饭局、赞助、处方量、"
             "范围外用法时，明确而友好地拒绝并转回学术（例如“这个我得婉拒，公司有规定，学术上的问题随时聊”）；"
             "时机合适时提出一个具体的下一步。"),
    "bad": ("水平较差：爱夸大和绝对化（比如保证有效、没有副作用），贬低竞品，必要时暗示范围外的用法；"
            "医生试探饭局、赞助或要支持时顺势答应并承诺放量；催促医生马上答应。"),
}
FALLBACK = {
    "good": ["您好，想先了解一下您门诊这类患者的情况。", "明白，我按说明书范围来说。", "那我下周再约您十五分钟，可以吗？"],
    "bad": ["我们这个药最好，没副作用，保证有效。", "别的药都不行，您早该换了。", "您今天就定下来吧。"],
}
TARGETS = ["S04", "S12", "S08", "S13"]
MAX_TURNS = 8
BAD_SIGNALS = {"accepted_benefit", "disclosed_stat", "promised_outcome", "evaded_boundary"}


class RepSay(BaseModel):
    say: str = Field(min_length=2, max_length=120)


def load(path, cls):
    f = Path(path)
    return [cls.model_validate_json(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]


def rep_say(provider, level, scenario, session, n) -> tuple[str, bool]:
    user = load_prompt("rep_bot").render(
        level_desc=LEVELS[level], rep_goal=scenario.rep_goal, context_brief=scenario.context_brief,
        pre_info=scenario.pre_info or "（无）", history=format_history(session.turns, 8))
    fb = FALLBACK[level][min(n, len(FALLBACK[level]) - 1)]
    out, degraded = structured_call(
        provider, prompt_name="rep_bot", system="你是严格输出 JSON 的角色扮演助手。",
        messages=[{"role": "user", "content": user}], model_cls=RepSay, fallback=RepSay(say=fb),
        max_retries=1, temperature=0.8)
    return out.say.strip(), degraded


def run(engine, provider, scenario, persona, level):
    sess = engine.start(scenario, persona, f"rep_sim_{level}")
    rep_fb = 0
    for i in range(MAX_TURNS):
        if sess.ended_at:
            break
        text, deg = rep_say(provider, level, scenario, sess, i)
        rep_fb += int(deg)
        engine.step(sess, scenario, persona, text)
    return sess, rep_fb


def final_trust(sess) -> int:
    return [t.state_after for t in sess.turns if t.state_after][-1].trust


def render(sess, label, rep_fb) -> list[str]:
    out = [f"### {label}｜结束原因：{sess.end_reason or '未结束'}｜代表兜底回合：{rep_fb}", ""]
    for t in sess.turns:
        st = f"　(信任{t.state_after.trust}/耐心{t.state_after.patience})" if t.state_after else ""
        if t.speaker == "rep":
            out.append(f"- **代表**：{t.text}　`{t.signals}`{st}")
        else:
            out.append(f"- **医生**：{t.text}　`意图={t.meta.get('intent')}`{st}")
    return out + [""]


def main() -> int:
    provider = get_provider()
    if provider.name == "mock":
        print("当前是 mock，无法做自适应模拟。请配置真实模型后再运行。")
        return 0
    try:
        kb = KnowledgeBase()
        kb = kb if kb.count() else None
    except Exception:  # noqa: BLE001
        kb = None
    engine = SessionEngine(provider, kb)
    personas = {p.id: p for p in load("data/personas/personas.jsonl", DoctorPersona)}
    scenarios = usable(load("data/scenarios/scenarios.jsonl", Scenario), load_review())
    chosen = [next((s for s in scenarios if s.skeleton_id == sid), None) for sid in TARGETS]
    chosen = [s for s in chosen if s]

    lines = ["# 样例对话（自适应代表模拟器）", "",
             f"- provider：{provider.name}｜知识库：{'有' if kb else '无'}｜{time.strftime('%Y-%m-%d %H:%M')}", ""]
    fails: list[str] = []
    all_turns: list = []
    wins = 0
    for s in chosen:
        p = personas[s.persona_id]
        lines += [f"## {s.id}｜{s.skeleton_id}｜{p.department}｜{p.difficulty}｜{s.type}", ""]
        res = {}
        for level in ("good", "bad"):
            sess, rep_fb = run(engine, provider, s, p, level)
            res[level] = sess
            all_turns += sess.turns
            lines += render(sess, "好代表" if level == "good" else "差代表", rep_fb)
            if count_false_ignored(sess.turns):
                fails.append(f"{s.id}/{level}：出现 {count_false_ignored(sess.turns)} 处“回避提问”误判")
            if count_repeats(sess.turns):
                fails.append(f"{s.id}/{level}：医生重复了 {count_repeats(sess.turns)} 句话")
        wins += int(final_trust(res["good"]) > final_trust(res["bad"]))
        sg, sb = signals_seen(res["good"].turns), signals_seen(res["bad"].turns)
        if s.skeleton_id == "S12":
            if "declined_boundary" not in sg:
                fails.append(f"{s.id}：好代表没有任何一次被识别为明确拒绝（declined_boundary）")
            if not (sb & BAD_SIGNALS):
                fails.append(f"{s.id}：差代表没有触发任何合规违规信号")
    if chosen and wins < len(chosen) - 1:
        fails.append(f"好代表信任度高于差代表的场景只有 {wins}/{len(chosen)}（要求至少 {len(chosen) - 1}）")
    avg, fb = avg_doctor_len(all_turns), fallback_rate(all_turns)
    if avg > 35:
        fails.append(f"医生平均字数 {avg:.1f} > 35")
    if fb > 0.2:
        fails.append(f"医生兜底率 {fb:.0%} > 20%")
    lines += ["## 汇总", "", f"- 好代表胜出：{wins}/{len(chosen)}", f"- 医生平均字数：{avg:.1f}",
              f"- 医生兜底率：{fb:.0%}", f"- 未通过项：{fails or '无'}", "", f"token 用量：{get_tracker().summary()}"]
    Path("docs/SAMPLE_SESSIONS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("已输出 docs/SAMPLE_SESSIONS.md；未通过项：", fails or "无")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
```

另外：`prompts/CHANGELOG.md` 追加 `rep_bot.md 0.1.0`；沿用 `scripts/run_real_gen.sh` 里连接 sutai Ollama 的方式运行 `python scripts/sim_session.py`。

**如果验收没通过**：把 `docs/SAMPLE_SESSIONS.md` 末尾的“未通过项”和对应的对话原文**原样汇报**。**不要降低判据，也不要为了通过去改脚本里的断言**；若是引擎问题，回到对应的卡（C2 到 C5）查原因。小模型的波动导致偶发失败时，可重跑一次，两次都失败才算失败。

## CARD C8 | 离线依赖包（服务器无外网） | deps: - | verify: . .venv/bin/activate && python scripts/extract_requirements.py --extras rag | head -3 && bash -n scripts/build_wheelhouse.sh && bash -n scripts/deploy.sh

**目标**：服务器无法访问 pypi，`make deploy` 在 pip 阶段会失败。建立离线依赖包机制：在有网的开发机预先下载，服务器离线安装。
**新建 2 个文件（原样写入，`chmod +x`）**：

`scripts/extract_requirements.py`
```python
"""从 pyproject.toml 提取第三方依赖（每行一个），供离线打包与服务器安装使用。
用法：python scripts/extract_requirements.py [--extras rag,dev]"""
import argparse
import sys
import tomllib
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--extras", default="", help="逗号分隔的可选依赖组，如 rag,dev")
    ap.add_argument("--pyproject", default="pyproject.toml")
    args = ap.parse_args()
    data = tomllib.loads(Path(args.pyproject).read_text(encoding="utf-8"))["project"]
    reqs = list(data.get("dependencies", []))
    optional = data.get("optional-dependencies", {})
    for name in [x for x in args.extras.split(",") if x]:
        if name not in optional:
            print(f"没有名为 {name} 的可选依赖组", file=sys.stderr)
            return 2
        reqs += optional[name]
    print("\n".join(dict.fromkeys(reqs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`scripts/build_wheelhouse.sh`
```bash
#!/usr/bin/env bash
# 在【有外网的开发机】上，为【无外网的服务器】预先下载依赖包到 wheelhouse/。
# 用法：bash scripts/build_wheelhouse.sh        （服务器为 Python 3.12 + x86_64 Linux；不同请用环境变量覆盖）
set -euo pipefail
cd "$(dirname "$0")/.."
PYV="${SERVER_PY:-3.12}"
ABI="cp${PYV/./}"
python3 scripts/extract_requirements.py --extras rag > /tmp/rep_trainer_req.txt
rm -rf wheelhouse && mkdir wheelhouse
pip download -r /tmp/rep_trainer_req.txt -d wheelhouse --only-binary=:all: \
  --python-version "$PYV" --implementation cp --abi "$ABI" \
  --platform manylinux2014_x86_64 --platform manylinux_2_17_x86_64 --platform manylinux_2_28_x86_64 \
  --platform manylinux_2_27_x86_64 --platform manylinux_2_34_x86_64 --platform linux_x86_64
echo "已下载 $(ls wheelhouse | wc -l) 个文件到 wheelhouse/（$(du -sh wheelhouse | cut -f1)）"
```

**改动点**
1. `scripts/deploy.sh`：把现有的 pip 安装步骤替换成（保留其他逻辑，包括 virtualenv 回退）：
```bash
# 依赖安装：优先离线 wheelhouse（服务器无外网），其次在线；都失败则沿用现有环境并明确告警
if ls wheelhouse/*.whl >/dev/null 2>&1; then
  python scripts/extract_requirements.py --extras rag > /tmp/rep_trainer_req.txt
  pip install --no-index --find-links wheelhouse -r /tmp/rep_trainer_req.txt \
    || echo "警告：离线安装失败，沿用现有依赖"
elif ! pip install -q -e ".[dev,rag]"; then
  echo "警告：没有 wheelhouse 且在线安装失败，沿用现有依赖（如新增了依赖，服务可能起不来）"
fi
```
2. `scripts/push_to_server.sh`：确认 rsync 的排除列表里**没有** `wheelhouse/`（它被 `.gitignore` 忽略，但需要传到服务器）。
3. `Makefile` 增加目标 `wheelhouse`（TAB 缩进，加进 `.PHONY`）：`bash scripts/build_wheelhouse.sh`。
4. 在 `docs/DEPLOY.md` 追加一节“离线依赖”：**只在新增或升级依赖时**，由人在有网的开发机运行 `make wheelhouse`，再 `make deploy`；当前没有新增依赖，所以暂时不需要。

**不要做**：不要运行 `build_wheelhouse.sh`（需要外网，且产物很大）；不要把 `wheelhouse/` 提交进仓库。
