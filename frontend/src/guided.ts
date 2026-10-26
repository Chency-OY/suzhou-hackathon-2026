import type { ScenarioDetail, ScenarioType } from "./types";

export type ChoiceQuality = "strong" | "partial" | "risk";

export interface GuidedChoice {
  text: string;
  quality: ChoiceQuality;
  feedback: string;
}

export interface GuidedStep {
  title: string;
  prompt: string;
  choices: GuidedChoice[];
}

type ChoiceSet = [GuidedChoice, GuidedChoice, GuidedChoice];

const choice = (text: string, quality: ChoiceQuality, feedback: string): GuidedChoice => ({ text, quality, feedback });

const opening: Record<ScenarioType, ChoiceSet> = {
  first_visit: [
    choice("感谢您抽时间。您目前在这类患者管理中最想解决什么问题？", "strong", "先征询医生的实际关注点，后续信息才有明确目标。"),
    choice("我先把这份资料从头到尾讲一遍，您听完再提问。", "partial", "资料可能有用，但没有先确认医生关切，容易占用时间。"),
    choice("今天主要想请您尽快把这款产品用于所有相关患者。", "risk", "不应催促具体诊疗决定，更不能暗示所有患者都适用。"),
  ],
  post_conference: [
    choice("您听完会议后，最想核对研究的哪部分：人群、终点，还是安全性？", "strong", "把讨论聚焦到医生要核对的证据，而不是预设结论。"),
    choice("会议结果很积极，我可以先把演示稿完整讲一遍。", "partial", "只讲积极结论而不先问具体疑问，容易遗漏研究局限。"),
    choice("会议已经证明它适合所有患者，细节不必再看。", "risk", "研究结论不能直接扩大为所有患者的适用结论。"),
  ],
  safety_concern: [
    choice("这个顾虑很重要。您主要担心哪类不良反应或哪类患者？我先确认问题。", "strong", "先明确风险问题和患者情境，再查对获批资料。"),
    choice("总体应该还好，我先给您讲讲产品优势。", "partial", "绕开安全顾虑会降低沟通质量，也没有回答医生的问题。"),
    choice("您放心，基本没有不良反应，不会影响用药。", "risk", "绝对化安全保证不可取，应准确说明已知风险与不确定性。"),
  ],
  competitor_compare: [
    choice("您希望比较哪类患者、哪个终点？我只按可核对的同口径资料回答。", "strong", "先确定比较条件，避免把不同研究直接当成头对头证据。"),
    choice("几种方案各有特点，我先介绍我们自己的资料。", "partial", "没有回应医生希望比较的具体问题。"),
    choice("竞品肯定不如我们，所有终点都是我们的方案更好。", "risk", "没有同口径证据时不能宣称全面优越，更不应贬低竞品。"),
  ],
  time_pressure: [
    choice("我知道您时间紧。能否用一分钟先了解您现在最关心的一个问题？", "strong", "先征得允许并聚焦一个问题，尊重医生的时间。"),
    choice("资料比较多，我尽量快速从第一页讲起。", "partial", "加快语速不等于聚焦，仍可能耽误医生。"),
    choice("再忙也请您听完，我必须把所有卖点讲完。", "risk", "施压式沟通不尊重医生的时间和选择。"),
  ],
  revisit_after_rejection: [
    choice("上次的交流似乎没解决您的顾虑。哪一点需要我先核实或补充？", "strong", "承认上次未解决的问题，并让医生决定这次交流重点。"),
    choice("我把上次的资料重新讲一遍，也许这次会更清楚。", "partial", "重复原来的讲法，没有先找出拒绝背后的原因。"),
    choice("您上次拒绝可能是误解了产品，这次应该改变决定。", "risk", "把异议归咎于医生并催促决定，容易损害信任。"),
  ],
  off_label_bait: [
    choice("这个问题涉及适用范围。我只能依据获批说明书回答；您想先核对哪项已获批信息？", "strong", "明确适用范围边界，同时继续帮助医生找到可核对的信息。"),
    choice("这个问题我暂时不回答，先继续介绍其他内容。", "partial", "避免越界是对的，但应说明核对路径，不能直接略过疑问。"),
    choice("虽然说明书没写，但按机制推测这类患者也可以使用。", "risk", "不能用机制推测代替获批适应症证据。"),
  ],
};

// Curated scenarios need replies to the doctor's actual first question, not a generic opener.
const openingById: Record<string, ChoiceSet> = {
  scn_002: [
    choice("今天只想了解您最需要哪类资料；如果现在不方便，我按您的问题整理后再发。", "strong", "一句话说明来意，并把交流范围和时间交给医生决定。"),
    choice("我尽量快讲，先给您看这套完整资料。", "partial", "讲得快仍未聚焦医生的问题。"),
    choice("只要两分钟，您必须先听完所有产品卖点。", "risk", "不能用时间压力要求医生接受完整推介。"),
  ],
  scn_005: [
    choice("不能直接画等号。要先核对研究采用的指标、临床终点和原文局限；您指的是哪项研究？", "strong", "先回应指标与结局并非天然等价，再核对具体研究。"),
    choice("会上讲的指标是积极的，我先把演示稿再讲一遍。", "partial", "没有回答指标能否代表临床结局。"),
    choice("指标改善就证明临床结局一定改善，不用看原文。", "risk", "不能把替代指标直接等同于临床获益。"),
  ],
  scn_008: [
    choice("有患者教育资料可供核对。患者最常卡在长期坚持的哪一步：理解方案、随访，还是其他问题？", "strong", "先回应资料需求，再找出实际教育难点。"),
    choice("有很多资料，我从第一份开始全部介绍。", "partial", "没有筛选适合基层患者沟通的内容。"),
    choice("只要用这个方案，患者长期坚持肯定没有问题。", "risk", "不能保证所有患者的长期依从性。"),
  ],
  scn_009: [
    choice("上次只讲有效性确实不完整。我会把安全性、不良反应和研究局限一起核对，您想先看哪一部分？", "strong", "承认遗漏，并把风险与局限纳入同一讨论。"),
    choice("安全性资料我下次再带，今天先继续讲有效性。", "partial", "再次绕开医生明确提出的安全问题。"),
    choice("只要有效，安全性和研究局限就不用讨论。", "risk", "不能忽视安全信息或研究限制。"),
  ],
  scn_011: [
    choice("这两份研究的人群和终点不同，不能直接排优劣。我可以先并列核对设计，再说明哪些结论有证据支持。", "strong", "正面回答不能直接比较，并给出客观核对方法。"),
    choice("我记得其中一份数字更好，可以先看那个。", "partial", "单看一个数字不足以判断不同研究的优劣。"),
    choice("只要数值更高，就能证明一种方案全面优于另一种。", "risk", "跨研究直接排名可能误导医生。"),
  ],
  scn_012: [
    choice("要看患者最常问什么：治疗目标、随访，还是风险？我按这个问题找可核对的患者沟通资料。", "strong", "把会议内容转化为医生实际能用的患者教育材料。"),
    choice("会议内容都很重要，我把幻灯片全发给您。", "partial", "没有筛选能回答患者问题的内容。"),
    choice("患者的问题不用解释，只要告诉他们照做就行。", "risk", "忽视患者理解与知情沟通不可取。"),
  ],
  scn_013: [
    choice("两份说明书分别对应成人体重管理和成人 2 型糖尿病的获批用途；具体适用条件与安全信息要分别按最新版说明书核对。您想先看哪一份？", "strong", "先答清两份说明书的用途，再保留具体条件与安全信息的核对边界。"),
    choice("两份说明书差不多，我先从产品亮点讲起。", "partial", "没有回答医生关于适用人群的直接问题。"),
    choice("两份说明书可以合起来看，所有超重或血糖异常患者都适用。", "risk", "不能合并不同适应症或扩大适用人群。"),
  ],
  scn_015: [
    choice("是否有直接比较以及对应研究人群、终点，我要按公开原文核对后回答；不能拿不同研究直接排名。", "strong", "不凭记忆编造研究，同时明确比较的证据边界。"),
    choice("我记得有直接比较，具体人群和终点晚些再查。", "partial", "尚未核实研究设计，就不宜先确认有直接证据。"),
    choice("直接比较不重要，任意两项研究的数值都能证明优劣。", "risk", "跨研究数字不能直接证明方案优劣。"),
  ],
};

function evidenceChoices(scenario: ScenarioDetail): ChoiceSet {
  const source = scenario.program_id === "xinermei" ? "获批说明书和已核实资料" : "已核实资料";
  switch (scenario.type) {
    case "safety_concern":
      return [
        choice(`我按${source}逐项回答已知风险；没有核实的部分先记录并补充资料。`, "strong", "准确区分已知风险与待核实信息，比笼统安慰更可靠。"),
        choice("常见情况一般可以处理，具体数字我回头再找。", "partial", "没有先提供可核对的安全资料，表述也过于笼统。"),
        choice("安全性没有问题，您无需再考虑这些反应。", "risk", "不能把安全风险说成不存在。"),
      ];
    case "competitor_compare":
      return [
        choice(`我先核对研究人群和终点，再用${source}说明能够直接比较的部分和局限。`, "strong", "比较应限定在可核对、同口径的证据范围内。"),
        choice("我记得我们的结果更好，但研究设计需要再查。", "partial", "尚未核实设计和数据时，不宜先给出优劣结论。"),
        choice("只看某一个有利数字就够了，其他终点可以忽略。", "risk", "选择性引用单个数字会误导比较。"),
      ];
    case "off_label_bait":
      return [
        choice("说明书之外的用法我不能推荐；我可以提供获批范围内的资料，并记录您的科学问题交由医学部门核实。", "strong", "保持推广边界，同时给医生一个合适的核实渠道。"),
        choice("这个用法我不确定，下次再说。", "partial", "承认不确定是对的，还应明确不能推荐说明书外使用，并给出核实路径。"),
        choice("虽然尚未获批，我们也可以按现有资料推断效果。", "risk", "不能将说明书外用途当成已获批推广结论。"),
      ];
    default:
      return [
        choice(`您提到的重点是这点。我按${source}回答能核实的部分，资料未覆盖的范围会明确说明。`, "strong", "紧扣医生关切，并把证据与不确定性讲清楚。"),
        choice("资料总体比较积极，细节我下次再补。", "partial", "缺少与医生问题直接对应的证据，也没有说明局限。"),
        choice("现有资料已经足够证明所有患者都会获益。", "risk", "不能把有限证据扩大成对所有患者的保证。"),
      ];
  }
}

const closing: ChoiceSet = [
  choice("您刚才关注的问题还有哪里没答清？如您愿意，我可以提供已核实资料，等您方便时再交流。", "strong", "先确认疑问是否解决，再由医生决定是否继续交流。"),
  choice("我今天先讲到这里，下次再来。", "partial", "结束时没有确认问题是否解决，也没有征求后续交流意愿。"),
  choice("那我们就定下来，请您尽快让所有这类患者使用。", "risk", "医药代表不应要求医生对患者作出统一用药承诺。"),
];

function rotate(choices: ChoiceSet, scenarioId: string, step: number): GuidedChoice[] {
  const offset = [...scenarioId].reduce((sum, letter) => sum + letter.charCodeAt(0), step) % choices.length;
  return [...choices.slice(offset), ...choices.slice(0, offset)];
}

export function guidedStep(scenario: ScenarioDetail, step: number): GuidedStep | null {
  if (step < 0 || step > 2) return null;
  const templates: [string, string, ChoiceSet][] = [
    ["先理解医生", "先看医生的原话：此刻你会怎么回应？", openingById[scenario.id] ?? opening[scenario.type]],
    ["回应关键问题", "医生提出关切后，怎样表达更稳妥？", evidenceChoices(scenario)],
    ["约定下一步", "结束前，你会怎么确认和安排后续交流？", closing],
  ];
  const [title, prompt, choices] = templates[step];
  return { title, prompt, choices: rotate(choices, scenario.id, step) };
}

export const QUALITY_LABEL: Record<ChoiceQuality, string> = {
  strong: "较稳妥", partial: "可以改进", risk: "需要避免",
};
