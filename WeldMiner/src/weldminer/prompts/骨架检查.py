"""
中文骨架检查与修正提示词
采用三段式 COT + Reflection 架构
"""

from typing import Any, Dict, List, Optional
import json

from ..models.data_schemas import format_direct_goal_list, format_sample_user_goal_list


def _build_source_block(source_text: Optional[str]) -> str:
    if source_text:
        return f"源文档文本:\n---\n{source_text}\n---"
    return (
        "源文档:\n---\n"
        "源文档以附图形式提供，请以附图为主进行核对与提取。\n---"
    )


OUTPUT_PATTERN = {
    "check_passed": bool,
    "problem_description": [],
    "corrected_results": [],
    "false_results": [],
    "missing_items": [],
    "missingitem_source": [],
}


def get_skeleton_check_prompt(
    skeleton_json: str,
    source_text: Optional[str],
    COT: str,
    diff_factors_example: str = "",
    sample_user_goal=None,
    sample_direct_goal=None,
) -> str:
    import json as _json

    source_block = _build_source_block(source_text)
    target_metrics = ", ".join(
        item for item in [format_sample_user_goal_list(sample_user_goal), format_direct_goal_list(sample_direct_goal)] if item
    )
    cot_block = (
        f"\n3. 第一步抽取过程产生的模型思考过程：{COT}"
        if COT and COT.strip()
        else ""
    )

    return f"""
你是一个精密的数据抽取质检专家。你的任务是对一份已完成的焊接工艺评定数据抽取结果进行**结构化验证**，而不是重新抽取数据。  
你将收到以下内容：
1. {source_block}
2. 第一步抽取的数据骨架 {skeleton_json}{cot_block}
你必须严格按照以下六个步骤执行验证，并在 `<think>` 标签中显式输出每一步的推理过程。思考结束后，再按指定 JSON 格式输出最终验证报告。
<think>
步骤1:根据每条数据输出结果中的 source_quote 定位到对应的数据位置，判断该数据内容是否符合逻辑。
步骤2:在对应的文本位置寻找数据或存在数据的来源图片，确认是否与抽取数据一致或是否图片来源一致，若不一致或未找到对应数据，记录为错误项,并记录错误原因,若为存疑项,记录为存疑项,并记录存疑原因,。
步骤3:列出文章中所有测试方法及其对应的数据
步骤4:识别每个测试方法产生的数据，判断是否包含用户目标指标：{target_metrics}。若无则不保留对应测试方法 
步骤5:检查接收到的数据是否遗漏了任何符合要求的测试方法或数据。同一焊接过程、相同测试条件和相同测试区域内的多个平行试样（例如试样1、试样2或C-1、C-2）必须合并为一个骨架条目，由下游性能抽取环节保存全部平行数值；不得把平行测量误判为遗漏骨架项。
步骤6:构建验证报告:
check_passed: bool 是否所有测试方法和数据都符合要求 如果有错误项或遗漏项则为 False
corrected_results: list[Dict[str, Any]] 检查为正确的数据条目
false_results: list[Dict[str, Any]] 检查为错误的数据条目
problem_description: list[str] 所有错误项的详细描述,与false_results顺序一一对应（无错误则为空列表）
missing_items: list[Dict[str, Any]] 检查为遗漏的测试方法或数据
missingitem_source: list[str] 每个检查为遗漏的数据的来源位置，填写方式为来源位置字符串列表，与missing_items顺序一一对应
反思验证阶段（自我检查） 在生成最终输出前，请对以下内容进行严格验证：
自检1: 数据定位是否准确，是否与原文位置一致？数据内容是否符合逻辑有无存在前后矛盾？如果存在定位错误，请记录为错误项。如存在定位模糊，请在 <think> 中标注并补充扫描。
自检2: 检查正确数据是否符合要求，如存在错误数据，请记录为错误项。
自检3: 检查是否遗漏了任何测试方法或数据，如存在遗漏风险，请在 <think> 中标注并补充扫描。
自检4: 检查是否只保留了符合要求的测试方法和数据，如存在错误风险，请在 <think> 中标注并补充扫描。
自检5: 检查接收到的数据是否遗漏了任何符合要求的测试方法或数据，如存在遗漏风险，请在 <think> 中标注并补充扫描。
自检6: 检查生成的验证报告是否符合要求，正确数据和错误数据是否与接收到的数据一致，如存在错误，请在 <think> 中标注并补充扫描。
回溯要求： 如果有任何检查节点没通过请重新从步骤1开始思考。
输出格式要求：你必须将回复分成两个部分：思考过程<think>和最终JSON数组<output>
</think>[在此完整输出你的思维链推理过程，包括所有步骤的填写内容和检查点结果。此部分用于可追溯性和调试。]
<output> [在此仅输出最终JSON数组，不要包含任何其他文字。] 
{OUTPUT_PATTERN}
</output> 若无数据，请在 <output> 中输出空数组[]"""



output_pattern2 = [
    {
        "data_features": "",
        "base_material": "",
        "filler_material": [],
        "welding_method": "",
        "source_quote": []
    }
]

def get_skeleton_correction_prompt(
    skeleton_json: str,
    COT: str,
    source_text: Optional[str],
    inspection_data: Dict[str, Any],
    diff_factors_example: str = "",
    lang: str = "zh",
) -> str:
    inspection_json = json.dumps(inspection_data, ensure_ascii=False, indent=2)
    source_block = _build_source_block(source_text)
    cot_block = (
        f"\n3. 第一步抽取过程产生的模型思考过程：{COT}"
        if COT and COT.strip()
        else ""
    )
    return f"""你是一个精密的数据抽取修正专家。你的任务是根据质检报告指出的具体错误和遗漏，对一份已完成的焊接工艺评定数据抽取结果进行**定向修正**，而不是重新抽取数据。

你将收到以下内容：
1. 原文：{source_block}
2. 第一步抽取的数据骨架：{skeleton_json}{cot_block}
4. 质检报告：{inspection_json}（包含 false_results、problem_description、missing_items、missingitem_source）
你必须严格按照以下六个步骤执行修正，并在 `<think>` 标签中显式输出每一步的推理过程。思考结束后，再按指定 JSON 格式输出修正后的完整数据骨架。
<think>
步骤1：解析质检报告中的错误项，逐条阅读质检报告中的 false_results 和 problem_description。明确每个错误项和其对应的错误原因。
步骤2：逐一修正错误项,回到原文中，根据质检报告指出的错误类型，重新定位正确的数据位置。提取正确的值，确保有原文精确引用句作为依据。在第一步抽取的数据骨架中对应位置直接替换错误值为正确值。
步骤3：解析质检报告中的遗漏项,逐条阅读质检报告中的 missing_items 和 missingitem_source。列出“待补全清单”.
步骤4：逐项补全遗漏数据,对“待补全清单”中的每一项,按照第一步抽取模型的输出结构规范，构造一个新的数据条目对象。
步骤5：处理补充的新数据条目对象，检查新数据条目是否与第一步抽取的数据骨架结构内容重复，若重复则删除新数据条目。将剩余的新数据条目追加到第一步抽取的数据骨架中末尾。
步骤6：构建修正后的完整数据骨架
必须输出唯一一份完整修正快照，不是增量修正项列表。完整快照中每个语义试样只能出现一次，不要同时保留修正前和修正后的两个版本；missing_items 已补入完整快照后不得再次单独追加。
data_features:str（必须包含：母材、焊材、焊接方法、测试条件、试样区域和试样编号）
base_material:List[str] (储存焊接母材的列表)
filler_material:List[Dict(str,str)] (列表中的每一个字典的KEY为焊接方式value为该焊接方式采用的焊材牌号)
welding_method: str (本条数据焊接试样采用的焊接类型)
source_quote:List[str]（列表中包含本焊接过程的每个元素所在语句，如在图表则为对应标题） 
注意:本阶段只构造试样的标识信息（base_material, filler_material, welding_method, data_features, source_quote），不提取具体的测试数值，用户目标指标数据由后续步骤专门提取 
反思验证阶段（自我检查）
在生成最终输出前，请对以下内容进行严格验证：
自检1：错误项是否全部修正？逐条核对质检报告的 false_results，确认每一项都已被处理（修改或删除）。如果有遗漏处理的错误项，立即补正。
自检2：修正后的值是否有原文依据？对每个被修改的字段，再次确认：新值在原文中存在精确引用。如果无法找到原文依据，标记为“修正失败”，保留原值。
自检3：是否根据质检报告中的 missing_items 和 missingitem_source，找到所有遗漏项？找到的遗漏项是否和来源位置一致？
自检4：遗漏项是否全部补全？核对质检报告的 missing_items，确认每一项都已在修正后的数组中存在对应条目。source_quote是否是正确对应？
自检5：检查修正和补全后的数据是否有重复项，如果有则删除重复项。判断重复时忽略措辞变化和自定义编号变化，按母材、焊材、焊接方法、测试条件和测试区域判断是否为同一语义试样；同一区域的平行测量只保留一个骨架条目。
自检6：输出格式兼容性确认输出为纯 JSON 数组，数据结构与第一步抽取的数据骨架结构完全相同并符合要求。
回溯要求：
如果自检1或自检4未通过（存在未处理的错误项或遗漏项），必须回到步骤1或步骤3重新处理。
如果自检2或自检3未通过，立即在思维链中修正对应字段并更新步骤6的输出，不需从头回溯。
如果经过一次回溯后仍有无法解决的问题（如原文歧义、数据缺失），不要无限循环，在对应条目添加 `_verification_note` 标记“需人工复核”并输出。
输出格式要求：
你必须将回复分成两个部分：思考过程 `<think>` 和最终 JSON 数组 `<output>`。
</think>
[在此完整输出你的思维链推理过程，包括每个步骤的处理细节、修正依据、自检结果。此部分用于可追溯性和调试。]
<output>
[在此仅输出修正后的完整 JSON 数组，结构必须与第一步 skeleton_json 完全一致，不要包含任何其他文字。]
</output>
若无数据，请在 <output> 中输出空数组 []。
"""


def get_prompt(skeleton_json: str, raw_text: str | None, COT: str) -> str:
    """
    兼容旧调用入口，等价于中文检查提示词。
    """
    return get_skeleton_check_prompt(
        skeleton_json=skeleton_json,
        source_text=raw_text,
        COT=COT,
    )
