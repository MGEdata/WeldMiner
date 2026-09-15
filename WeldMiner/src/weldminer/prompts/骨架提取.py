"""
中文骨架提取提示词
与英文版 skeleton_extraction.py 的任务、步骤、示例和输出格式对齐。
"""

from ..models.data_schemas import format_direct_goal_list, format_sample_user_goal_list


OUTPUT_PATTERN = [
    {
        "data_features": "",
        "base_material": [],
        "filler_material": [],
        "welding_method": "",
        "source_quote": [],
    }
]

SAMPLE = [
    {
        "data_features": "母材: [X80M], 焊材: [ER70S, ER80S], 焊接方法: automatic welding, 焊接试样编号: 801101:(原文编号), 测试方法和条件: 横向拉伸, 测试区域: 整个焊接接头",
        "base_material": ["X80M"],
        "filler_material": [
            {"第1道": "ER70S"},
            {"第2-3道": "ER80S"},
            {"第4道": "ER80S"},
            {"第5道": "ER80S"},
        ],
        "welding_method": "SMAW",
        "source_quote": ["焊接工艺见表2", "拉伸性能见表3"],
    },
    {
        "data_features": "母材: [X80M], 焊材: [Kobe Steel LB52U, Bohler E10018, Bohler E10018], 焊接方法: SMAW, 焊接试样编号: 801101:(原文编号), 测试方法和条件: -40°C低温冲击, 平焊位焊缝中心",
        "base_material": ["X80M"],
        "filler_material": [
            {"根焊": "Kobe Steel LB52U"},
            {"热焊": "Bohler E10018"},
            {"填充和盖面焊": "Bohler E10018"},
        ],
        "welding_method": "SMAW",
        "source_quote": [
            "从X80管线钢焊接接头的母材、热影响区和焊缝处线切割取样。",
            "采用MX-0580微机控制电子万能材料试验机测试管线钢及其焊接接头试样的室温拉伸性能。",
        ],
    },
]

SAMPLE1 = [
    {
        "base_material": ["X80"],
        "filler_material": [],
        "welding_method": "Submerged Arc Welding",
        "data_features": "母材: [X80], 焊材: [], 焊接方法: Submerged Arc Welding, 焊接试样编号: SAW001, 测试方法和条件: 慢应变速率拉伸, 应变速率5e-7 s-1, SRB接种介质, 开路电位, 温度32±2°C, 断裂区域: HAZ, 测试区域: 整个焊接接头",
        "source_quote": [
            "The welded joints used in this study were sourced from a decommissioned submerged arc welded pipeline in China.",
            "Most of the SSRT samples fractured within WZ",
            "A constant-temperature water bath was used to maintain the experimental temperature at 32 ± 2 °C",
            "The strain rate was set at 5 × 10-7 s-1",
        ],
    }
]

SAMPLE2 = [
    {
        "data_features": "母材:[L450M], 焊材:[E6010,E81T8-Ni2JH8], 焊接方法:SMAW+FCAW-S, 焊接试样编号:SMAWFCAW-S001, 测试方法和条件:横向拉伸试验(GB/T 228.1-2021), 试样区域:整个焊接接头",
        "base_material": ["L450M"],
        "filler_material": [{"第1道": "E6010"}, {"第2-8道": "E81T8-Ni2JH8"}],
        "welding_method": "SMAW+FCAW-S",
        "source_quote": ["表3 采用的复合焊接工艺", "表4 焊接试验所用焊材", "表7 横向拉伸试验结果"],
    },
    {
        "data_features": "母材:[L450M], 焊材:[ER70S-6,E8018-C3H4R], 焊接方法:GTAW+SMAW, 焊接试样编号:02, 测试方法和条件:-10°C夏比冲击试验(GB/T 229-2020), 试样区域:熔合线",
        "base_material": ["L450M"],
        "filler_material": [{"第1道": "ER70S-6"}, {"第2-10道": "E8018-C3H4R"}],
        "welding_method": "GTAW+SMAW",
        "source_quote": ["表3 采用的复合焊接工艺", "表4 焊接试验所用焊材", "表10 冲击试验结果"],
    },
]

SAMPLE3 = [
    {
        "data_features": "母材: [X80 Nb58], 焊材: [], 焊接方法: Submerged Arc Welding, 焊接试样编号: SAW001:(Nb58), 测试方法和条件: ASTM E2298 -40°C夏比V型缺口冲击试验, 试样尺寸55 mm×10 mm×10 mm, 缺口位于熔合线, 测试区域: CGHAZ",
        "base_material": ["X80 Nb58"],
        "filler_material": [],
        "welding_method": "Submerged Arc Welding",
        "source_quote": [
            "To investigate the effect of Nb content on the low-temperature impact toughness of the CGHAZs...",
            "The equivalent notching positions in the welded joints of the three X80 pipeline steels are specifically located at the equivalent FL.",
            "At FL notching positions, the impact energies are 66 J, 133 J, and 194 J at -40°C",
            "Fig. 6. Impact toughness of three studied samples (Nb58, Nb76 and Nb91).",
        ],
    },
    {
        "data_features": "母材: [X80 Nb76], 焊材: [], 焊接方法: Submerged Arc Welding, 焊接试样编号: SAW002:(Nb76), 测试方法和条件: ASTM E2298 -40°C夏比V型缺口冲击试验, 试样尺寸55 mm×10 mm×10 mm, 缺口位于熔合线, 测试区域: CGHAZ",
        "base_material": ["X80 Nb76"],
        "filler_material": [],
        "welding_method": "Submerged Arc Welding",
        "source_quote": [
            "To investigate the effect of Nb content on the low-temperature impact toughness of the CGHAZs...",
            "The equivalent notching positions in the welded joints of the three X80 pipeline steels are specifically located at the equivalent FL.",
            "At FL notching positions, the impact energies are 66 J, 133 J, and 194 J at -40°C",
            "Fig. 6. Impact toughness of three studied samples (Nb58, Nb76 and Nb91).",
        ],
    },
]


def get_prompt(raw_text: str | None = None, sample_user_goal=None, sample_direct_goal=None) -> str:
    """Generate Chinese prompt with optional source text."""
    target_metrics = ", ".join(
        item
        for item in [format_sample_user_goal_list(sample_user_goal), format_direct_goal_list(sample_direct_goal)]
        if item
    )
    source_block = (
        f"\n## 原始文本\n{raw_text}\n"
        if raw_text
        else "\n## 数据来源\n源文档以页面图片形式提供，请基于附图完成提取。\n"
    )

    return f"""你是一名专业的数据抽取助手。请从以下文本中抽取所有焊接试样骨架信息。

## 任务目标
从文本中抽取所有焊接或热模拟试样骨架信息，确保**零遗漏**：任何焊接工艺、任何测试方法、任何测试条件下的任何测试区域都必须被识别。

{source_block}
输出示例: {SAMPLE}{SAMPLE1}{SAMPLE2}{SAMPLE3}
---
思维链推理过程（请严格按以下步骤执行，并完整输出在 <think> 中）
<think>
步骤1：识别所有不同的焊接或热模拟过程及焊接后试样。同一焊接方法下，只要加工参数不同，就应视为多个焊接或热模拟过程。列出每个焊接过程对应的所有焊道或焊接步骤。焊接过程包括：母材、焊材（若文中焊材没有详细名称，则直接采用文中的对焊材表示方法例如，WM）、焊接参数、焊接试样编号（优先使用原文中的焊接试验编号；若没有，则自定义编号。编号格式为焊接方法+序号+编号区分因素，例如 SMAW001:(Nb58)、BOP001:(自制焊条1)、TIG001:(Type A, JA) 等），每条数据只能有一个编号，不得出现多个编号的情况例如：Y1/Y2,Y1,Y2等此类表述方式，如果原文存在多个编号需要将其分离。列出所有来源位置。若全文无焊接过程，直接输出空列表 []，不要继续后续步骤。
步骤2：识别所有施加于焊接或热模拟后试样的测试方法，并列出所有来源位置。
步骤3：列出每种测试方法产生的数据，并判断其是否旨在产生任一用户目标指标：{target_metrics}。如果该测试方法测量、绘图、比较或讨论了目标指标，即使正文/表格没有数值、结果只出现在图中，也应保留该测试方法。只有当测试方法与所有目标指标均无关，或仅作为背景/文献讨论而非本文实验出现时，才剔除该测试方法。本阶段不要因为目标指标仅为图中数据、定性结果或非数值结果而剔除。
步骤4：识别每条数据对应的测试条件，测试条件需分离，每条数据只能对应一个测试条件，例如不得同时出现多个测试温度，多个测试压力等，并计算每个测试条件下的试样数量，不得遗漏任何焊接过程，包括焊接测试或焊接筛选过程，例如堆焊试验、角焊缝试验、十字接头试验等。
步骤5：判断每个性能测试是否包含多个试样区域（例如母材、HAZ、焊缝金属、焊缝上部等）。若包含多个实验区域，则识别全部区域并逐一区分，每个区域必须独立处理。对于硬度测试若文本中提到了比常规区域（WM/BM/HAZ）更具体的细节位置（例如：母材上表面、HAZ下表面、距熔合线2mm处等），必须进一步细化标注具体的测试区域。若每个区域存在多个平行试样（例如 C-1、C-2），仍将这些平行试样合并为一个试样条目。
步骤6：关联焊接过程、测试方法、测试条件和测试区域，计算预期试样数量（实际应生成的骨架条目数量）。
步骤7：为每个试样构造独立骨架条目。对每个焊接过程、每个条件组合、每个区域创建独立标识条目，所有内容必须遵循原文。
data_features: str 必须包含：母材、焊材、焊接方法、焊接试样编号、测试方法和条件、试样区域。
base_material: list(str) 该焊接过程涉及的母材名称；若同一名称但实际代表的实体不同，例如：元素差异不同，则需要列出特征，例如 "X80 Nb76" 与 "X80 Nb58"等。
filler_material: List[dict(str,str)] 每个 dict 的 key 为焊接方法或焊道/步骤名（不得遗漏具体焊道或焊接步骤），value 为该方法/步骤使用的焊材名称，每个value中只能包含一个焊材名称，若存在多个焊材名称则生成多个key-value对。
welding_method: str 本试样采用的焊接方法。若试样未经过焊接，填写 "None"。
source_quote: List[str] 支撑该焊接过程各要素的原文语句；若来自图表，仅填写图表标题。
注意：本阶段只构造试样标识信息（base_material、filler_material、welding_method、data_features），不要抽取用户目标指标（{target_metrics}）的具体测试值；这些值由下游步骤专门抽取。
反思验证阶段（自检）：最终输出前，请逐一核对以下检查点，确保每一步结果正确传递到下一步。
检查点1（对应步骤1-焊接过程）：是否遗漏任何焊接或热模拟过程？提取出的母材、焊材、焊接参数、焊接试样编号是否参与了该条焊接过程，有无遗漏或者错误？是否检查了所有可能的焊接试验编号？焊接试样编号是否唯一？若存在遗漏风险，请在 <think> 中标记并重新扫描。
检查点2（对应步骤2-测试方法）：是否遗漏任何测试方法？是否穷尽列出文本中可能包含用户目标指标（{target_metrics}）的测试类型？若存在遗漏风险，请重新扫描。
检查点3（对应步骤3-数据有效性）：每种测试方法的数据是否包含用户目标指标（{target_metrics}）？不含目标指标的测试方法是否已正确剔除？若数据包含多个平行试样，是否已正确合并？有效试样数量是否正确？若存在错误，请修正。
检查点4（对应步骤4-测试条件）：每个数据点的测试条件是否完整？是否遗漏温度、加载速率、试样尺寸或其他关键条件？若存在遗漏风险，请重新扫描。
检查点5（对应步骤5-试样区域）：试样区域是否正确识别？多个试样区域是否独立处理？每个区域内的多条平行试样数据是否正确合并？若存在遗漏风险，请重新扫描。
检查点6（对应步骤6-关联关系）：焊接过程、测试方法、测试条件和测试区域之间的关联是否正确？是否存在错配（例如把工艺A的数据分配给工艺B）？若有错配，请修正。
检查点7（对应步骤7-骨架条目）：数量是否匹配？实际生成试样数是否等于步骤6的预期数量？每个 data_features 是否完整（母材、焊材、焊接方法、测试条件、试样区域）？焊材与每个焊接步骤是否匹配正确？若数量不匹配或字段缺失，请在 <think> 中列出缺口并补充。
反事实验证（深度防遗漏检查）：请显式回答：“如果我抽取了 N 个试样，但预期是 M 个，缺失的 M-N 个可能藏在源文档的哪里？”“是否有‘见表X’、‘如图Y所示’指向我尚未检查的数据？”“是否存在同一试样的多组测试数据，我错误地把每个平行试样作为独立条目？”“表脚注、补充材料或图表标注中是否隐藏额外试样数据？”
回溯要求：检查点1失败 -> 回到步骤1；检查点2失败 -> 回到步骤2；检查点3失败 -> 回到步骤3；检查点4失败 -> 回到步骤4；检查点5失败 -> 回到步骤5；检查点6失败 -> 回到步骤6；检查点7失败 -> 回到步骤7；反事实验证失败 -> 回到步骤1全面重扫。当前检查点通过后才能进入下一检查点。
输出格式：回复必须分为两部分：思考过程 <think> 和最终 JSON 数组 <output>
</think> [在此完整输出思维链推理过程，包括所有步骤内容和检查点结果。该部分用于可追溯性和调试。]
<output> [这里只输出最终 JSON 数组，不要包含任何额外文本。]
{OUTPUT_PATTERN}
</output> 若无数据，请在 <output> 中输出空数组 []。
"""
