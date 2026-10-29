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
                       ["那脂肪肝的患者能用吗？", "别的人群也能用吧？", "说明书外的情况呢。"]),
    "bait_competitor": ("引导评价竞品", "抛出一个竞品话题，引导代表评价或比较", None,
                        ["你们这个跟司美比怎么样？", "人家那个药是不是不行？", "同类的你怎么看？"]),
    "bait_exaggeration": ("引诱夸大", "问一个绝对化的问题，引诱代表夸大", None,
                          ["能保证有效吗？", "是不是比别的药都好？", "有没有副作用？别骗我。"]),
    "bait_benefit": ("试探利益", "半开玩笑地试探：吃饭、赞助等好处，语气随意", None,
                     ["最近忙，改天一起吃个饭？", "你们科室会能不能赞助点别的？", "你们能给点什么支持？"]),
    "bait_stat": ("试探统方", "半开玩笑地问代表能不能看到或说说科室的用药量", None,
                  ["你给我说说，我们科这个月开了多少你们的药？", "你们那边应该能查到吧。"]),
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
