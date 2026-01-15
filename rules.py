"""
中医体质判定规则系统
基于《中医体质分类与判定》九种体质标准
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import re
import math


@dataclass
class KeywordMatch:
    """关键词匹配结果"""
    keyword: str
    weight: float
    span: str  # 匹配到的文本片段


@dataclass
class ConstitutionEvidence:
    """体质判定证据"""
    type: str
    score: float
    matched: List[KeywordMatch]


class ConstitutionRulebook:
    """体质判定规则库"""
    
    def __init__(self):
        self.rules = self._build_rules()
    
    def _build_rules(self) -> Dict[str, Dict]:
        """构建九种体质的规则库"""
        return {
            "平和质": {
                "keywords": {
                    # 正面特征
                    "精力充沛": 3, "精神好": 3, "体力好": 3, "不易疲劳": 3,
                    "睡眠好": 3, "睡眠安稳": 3, "入睡快": 2, "睡眠质量好": 3,
                    "二便正常": 3, "大便正常": 3, "小便正常": 2, "排便规律": 2,
                    "舌淡红": 2, "苔薄白": 2, "舌苔正常": 2,
                    "情绪稳定": 2, "心情好": 2, "不易生气": 2,
                    "食欲好": 2, "消化好": 2, "不易感冒": 2, "抵抗力好": 2,
                },
                "negatives": {
                    "乏力": -2, "疲劳": -2, "怕冷": -2, "怕热": -2,
                    "失眠": -2, "便秘": -2, "腹泻": -2, "易感冒": -2,
                },
                "explanation": "平和质是理想的健康体质，表现为精力充沛、睡眠良好、二便正常、情绪稳定。",
                "common_questions": ["是否容易疲劳？", "睡眠质量如何？", "二便是否正常？"]
            },
            
            "气虚质": {
                "keywords": {
                    "容易疲劳": 4, "乏力": 4, "没力气": 4, "疲倦": 3, "累": 3,
                    "气短": 4, "懒言": 3, "不想说话": 3, "说话声音低": 2,
                    "自汗": 3, "容易出汗": 3, "动则汗出": 3, "出汗多": 2,
                    "易感冒": 4, "经常感冒": 3, "抵抗力差": 3, "免疫力低": 2,
                    "食欲不振": 2, "不想吃饭": 2, "腹胀": 2,
                    "舌淡": 2, "舌边有齿痕": 2, "苔白": 1,
                    "面色苍白": 2, "面色萎黄": 2,
                },
                "negatives": {
                    "精力充沛": -3, "体力好": -3, "不易疲劳": -3,
                    "怕热": -2, "五心烦热": -2, "盗汗": -2,
                },
                "explanation": "气虚质以元气不足、容易疲乏、气短懒言为主要特征。",
                "common_questions": ["是否容易疲劳？", "是否容易出汗？", "是否容易感冒？", "说话声音如何？"]
            },
            
            "阳虚质": {
                "keywords": {
                    "怕冷": 5, "畏寒": 5, "手脚冷": 4, "手脚冰凉": 4, "四肢不温": 3,
                    "喜热饮": 4, "喜欢热饮": 3, "喝热水": 3, "不敢吃凉的": 3,
                    "精神不振": 3, "精神萎靡": 3, "嗜睡": 2,
                    "便溏": 3, "大便不成形": 3, "腹泻": 2, "拉肚子": 2,
                    "腰膝酸软": 3, "腰酸": 2, "腿软": 2,
                    "面色苍白": 2, "舌淡": 2, "苔白": 2, "舌胖大": 2,
                    "夜尿多": 2, "小便清长": 2,
                    "性欲减退": 1, "月经推迟": 1,
                },
                "negatives": {
                    "怕热": -4, "五心烦热": -4, "盗汗": -4, "口干": -2,
                    "喜冷饮": -3, "便秘": -2, "大便干": -2,
                },
                "explanation": "阳虚质以阳气不足、畏寒怕冷、手足不温为主要特征。",
                "common_questions": ["是否怕冷？", "手脚是否冰凉？", "是否喜欢热饮？", "大便情况如何？"]
            },
            
            "阴虚质": {
                "keywords": {
                    "口干": 4, "咽燥": 4, "口燥咽干": 4, "口渴": 3, "想喝水": 2,
                    "五心烦热": 4, "手心热": 3, "脚心热": 3, "手足心热": 3,
                    "盗汗": 4, "夜间出汗": 3, "睡觉出汗": 3,
                    "便干": 3, "便秘": 3, "大便干结": 3, "大便困难": 2,
                    "失眠": 3, "入睡困难": 2, "多梦": 2,
                    "舌红": 3, "少苔": 3, "无苔": 2, "苔少": 2,
                    "皮肤干燥": 2, "眼干": 2, "眼涩": 2,
                    "易怒": 2, "烦躁": 2, "脾气大": 2,
                },
                "negatives": {
                    "怕冷": -4, "畏寒": -4, "手脚冷": -4,
                    "便溏": -3, "腹泻": -3, "舌淡": -2, "苔白厚": -2,
                },
                "explanation": "阴虚质以阴液亏少、口燥咽干、手足心热为主要特征。",
                "common_questions": ["是否口干？", "是否怕热？", "夜间是否出汗？", "大便是否干燥？"]
            },
            
            "痰湿质": {
                "keywords": {
                    "体胖": 4, "肥胖": 4, "超重": 3, "体重超标": 3,
                    "困重": 3, "身体困重": 3, "沉重感": 2, "乏力": 2,
                    "痰多": 4, "有痰": 3, "咳痰": 3, "痰多黏腻": 3,
                    "胸闷": 3, "胸脘痞闷": 3, "胸口闷": 2,
                    "苔腻": 4, "苔厚腻": 4, "舌苔厚": 3, "苔白腻": 3,
                    "口黏": 3, "口中黏腻": 3, "口甜": 2,
                    "大便黏": 3, "大便不成形": 2, "便溏": 2,
                    "嗜睡": 2, "爱睡觉": 2, "容易困": 2,
                    "腹部肥满": 2, "肚子大": 2,
                },
                "negatives": {
                    "消瘦": -3, "体瘦": -3, "体重轻": -2,
                    "口干": -2, "便干": -2, "便秘": -2,
                },
                "explanation": "痰湿质以痰湿凝聚、体形肥胖、腹部肥满、口黏苔腻为主要特征。",
                "common_questions": ["体型如何？", "是否有痰？", "舌苔是否厚腻？", "是否感觉身体困重？"]
            },
            
            "湿热质": {
                "keywords": {
                    "口苦": 4, "口黏": 3, "口中黏腻": 3, "口臭": 2,
                    "痤疮": 4, "长痘": 3, "痘痘": 3, "粉刺": 2,
                    "尿黄": 3, "小便黄": 3, "尿赤": 2,
                    "苔黄腻": 4, "舌苔黄腻": 4, "苔黄": 3,
                    "身热": 3, "身体发热": 2, "烦躁": 2,
                    "大便黏腻": 3, "大便不爽": 2, "肛门灼热": 2,
                    "白带多": 2, "白带黄": 2, "带下多": 1,
                    "面垢": 2, "面色发黄": 2, "油光满面": 2,
                },
                "negatives": {
                    "怕冷": -3, "畏寒": -3, "手脚冷": -3,
                    "便溏": -2, "舌淡": -2, "苔白": -2,
                },
                "explanation": "湿热质以面垢油腻、口苦、苔黄腻、易长痤疮为主要特征。",
                "common_questions": ["是否有口苦？", "是否长痤疮？", "舌苔是否黄腻？", "小便颜色如何？"]
            },
            
            "血瘀质": {
                "keywords": {
                    "刺痛": 4, "固定痛": 3, "疼痛固定": 3,
                    "色斑": 4, "长斑": 3, "黄褐斑": 2, "老年斑": 1,
                    "唇暗": 3, "嘴唇暗": 3, "唇色暗": 2,
                    "舌紫暗": 4, "舌有瘀点": 4, "舌有瘀斑": 3, "舌下静脉曲张": 3,
                    "肌肤甲错": 3, "皮肤粗糙": 2, "皮肤干燥": 2,
                    "健忘": 2, "记忆力差": 2,
                    "痛经": 2, "月经有血块": 2, "经色暗": 2,
                    "易烦躁": 2, "易怒": 1,
                },
                "negatives": {
                    "面色红润": -2, "唇色红润": -2, "舌淡红": -2,
                },
                "explanation": "血瘀质以血行不畅、肤色晦暗、舌质紫暗为主要特征。",
                "common_questions": ["是否有色斑？", "唇色如何？", "是否有固定疼痛？", "舌质颜色如何？"]
            },
            
            "气郁质": {
                "keywords": {
                    "情绪抑郁": 4, "抑郁": 4, "心情不好": 3, "情绪低落": 3,
                    "易叹气": 4, "爱叹气": 3, "经常叹气": 3,
                    "胸胁胀": 3, "胸胁胀痛": 3, "两胁胀痛": 3, "胸闷": 2,
                    "咽中异物感": 3, "梅核气": 3, "喉咙有东西": 2, "咽部不适": 2,
                    "失眠": 3, "入睡困难": 2, "多梦": 2,
                    "易紧张": 2, "焦虑": 2, "担心": 2, "思虑多": 2,
                    "食欲不振": 2, "不想吃饭": 2,
                    "月经不调": 2, "痛经": 1,
                },
                "negatives": {
                    "情绪稳定": -3, "心情好": -3, "开朗": -2,
                },
                "explanation": "气郁质以神情抑郁、情感脆弱、烦闷不乐为主要特征。",
                "common_questions": ["情绪如何？", "是否容易叹气？", "是否有胸闷？", "睡眠如何？"]
            },
            
            "特禀质": {
                "keywords": {
                    "过敏": 5, "过敏体质": 5, "容易过敏": 4,
                    "鼻炎": 4, "过敏性鼻炎": 4, "鼻塞": 2, "打喷嚏": 2,
                    "荨麻疹": 4, "风疹": 3, "皮肤过敏": 3, "湿疹": 2,
                    "对气味敏感": 3, "闻不得味": 2, "气味过敏": 2,
                    "对食物敏感": 3, "食物过敏": 3, "不能吃某些食物": 2,
                    "哮喘": 3, "过敏性哮喘": 3,
                    "遗传": 2, "家族史": 2, "父母过敏": 1,
                },
                "negatives": {
                    "不过敏": -3, "无过敏史": -3,
                },
                "explanation": "特禀质以先天失常、过敏反应为主要特征。",
                "common_questions": ["是否有过敏史？", "是否有鼻炎或荨麻疹？", "对什么过敏？"]
            },
        }
    
    def match_keywords(self, text: str, constitution_type: str) -> List[KeywordMatch]:
        """匹配文本中的关键词"""
        matches = []
        rule = self.rules.get(constitution_type)
        if not rule:
            return matches
        
        text_lower = text.lower()
        
        # 匹配关键词
        for keyword, weight in rule["keywords"].items():
            # 简单的包含匹配（可扩展为正则或更复杂的分词）
            if keyword in text or keyword in text_lower:
                # 尝试提取匹配的片段（前后各10个字符）
                idx = text.find(keyword)
                if idx == -1:
                    idx = text_lower.find(keyword)
                if idx != -1:
                    start = max(0, idx - 10)
                    end = min(len(text), idx + len(keyword) + 10)
                    span = text[start:end]
                    matches.append(KeywordMatch(keyword=keyword, weight=weight, span=span))
        
        return matches
    
    def calculate_score(self, text: str, constitution_type: str) -> Tuple[float, List[KeywordMatch]]:
        """计算体质得分"""
        rule = self.rules.get(constitution_type)
        if not rule:
            return 0.0, []
        
        score = 0.0
        matches = self.match_keywords(text, constitution_type)
        
        # 正分：关键词匹配
        for match in matches:
            score += match.weight
        
        # 负分：反证匹配
        text_lower = text.lower()
        for negative, penalty in rule["negatives"].items():
            if negative in text or negative in text_lower:
                score += penalty  # penalty 已经是负数
        
        return max(0.0, score), matches
    
    def normalize_confidence(self, scores: Dict[str, float]) -> Dict[str, float]:
        """将得分归一化为置信度（使用 softmax-like 方法）"""
        if not scores:
            return {}
        
        # 使用 score / (score + K) 方法，K=10 作为平滑参数
        K = 10.0
        confidences = {}
        for const_type, score in scores.items():
            confidences[const_type] = score / (score + K)
        
        # 也可以使用 softmax（可选）
        # total = sum(math.exp(s) for s in scores.values())
        # confidences = {k: math.exp(v) / total for k, v in scores.items()}
        
        return confidences
    
    def analyze(self, text: str) -> Dict:
        """分析文本，返回体质判定结果"""
        if not text or len(text.strip()) < 5:
            return {
                "primary_type": "信息不足",
                "confidence": 0.0,
                "reason": "输入文本过短，无法进行有效判定"
            }
        
        # 计算所有体质的得分
        all_scores = {}
        all_evidence = {}
        
        for const_type in self.rules.keys():
            score, matches = self.calculate_score(text, const_type)
            all_scores[const_type] = score
            all_evidence[const_type] = ConstitutionEvidence(
                type=const_type,
                score=score,
                matched=matches
            )
        
        # 归一化置信度
        confidences = self.normalize_confidence(all_scores)
        
        # 找到最高分
        if not all_scores:
            return {
                "primary_type": "信息不足",
                "confidence": 0.0,
                "reason": "无法匹配到任何体质特征"
            }
        
        sorted_types = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        primary_type, primary_score = sorted_types[0]
        
        # 阈值判断：如果最高分太低，返回信息不足
        MIN_SCORE_THRESHOLD = 3.0
        if primary_score < MIN_SCORE_THRESHOLD:
            return {
                "primary_type": "信息不足",
                "confidence": 0.0,
                "reason": f"最高得分 {primary_score:.1f} 低于阈值 {MIN_SCORE_THRESHOLD}",
                "all_scores": all_scores,
                "evidence": all_evidence
            }
        
        # 找到次要体质（分差在阈值内的前2个）
        secondary_types = []
        SECONDARY_THRESHOLD = 5.0  # 分差阈值
        for const_type, score in sorted_types[1:3]:  # 取第2、3名
            if primary_score - score <= SECONDARY_THRESHOLD and score > 0:
                secondary_types.append(const_type)
        
        return {
            "primary_type": primary_type,
            "secondary_types": secondary_types,
            "confidence": confidences.get(primary_type, 0.0),
            "primary_score": primary_score,
            "all_scores": all_scores,
            "evidence": all_evidence
        }
    
    def get_recommendations(self, constitution_type: str) -> Dict[str, List[str]]:
        """获取体质的生活建议"""
        recommendations = {
            "平和质": {
                "lifestyle": [
                    "保持规律作息，早睡早起",
                    "适度运动，如散步、慢跑、太极拳",
                    "保持心情愉悦，避免过度劳累"
                ],
                "diet": [
                    "饮食均衡，不偏食",
                    "可适量食用各类食物，保持营养平衡",
                    "避免暴饮暴食"
                ],
                "when_to_seek_help": [
                    "如出现明显不适症状，建议咨询专业中医师"
                ]
            },
            "气虚质": {
                "lifestyle": [
                    "避免过度劳累，注意休息",
                    "适度运动，以不感到疲劳为宜，如散步、太极拳",
                    "保证充足睡眠，避免熬夜"
                ],
                "diet": [
                    "可适当食用补气食物，如山药、大枣、小米等",
                    "避免生冷、寒凉食物",
                    "饮食规律，少食多餐"
                ],
                "when_to_seek_help": [
                    "如疲劳感持续加重，建议咨询专业中医师"
                ]
            },
            "阳虚质": {
                "lifestyle": [
                    "注意保暖，尤其是腹部和足部",
                    "适度运动，以温和运动为主，如慢跑、太极拳",
                    "多晒太阳，避免长时间待在寒冷环境"
                ],
                "diet": [
                    "可适当食用温阳食物，如羊肉、生姜、桂圆等",
                    "避免生冷、寒凉食物和冷饮",
                    "饮食宜温热"
                ],
                "when_to_seek_help": [
                    "如畏寒症状明显，建议咨询专业中医师"
                ]
            },
            "阴虚质": {
                "lifestyle": [
                    "避免熬夜，保证充足睡眠",
                    "适度运动，避免剧烈运动，可选择瑜伽、散步",
                    "保持心情平静，避免急躁"
                ],
                "diet": [
                    "可适当食用滋阴食物，如银耳、百合、梨等",
                    "避免辛辣、燥热食物",
                    "多喝水，饮食宜清淡"
                ],
                "when_to_seek_help": [
                    "如口干、失眠等症状明显，建议咨询专业中医师"
                ]
            },
            "痰湿质": {
                "lifestyle": [
                    "适度运动，以有氧运动为主，如快走、游泳",
                    "避免久坐，多活动",
                    "保证充足睡眠，但避免过度嗜睡"
                ],
                "diet": [
                    "饮食清淡，可适当食用健脾祛湿食物，如薏米、冬瓜、白萝卜等",
                    "避免油腻、甜腻、生冷食物",
                    "控制食量，避免暴饮暴食"
                ],
                "when_to_seek_help": [
                    "如体重持续增加或痰多症状明显，建议咨询专业中医师"
                ]
            },
            "湿热质": {
                "lifestyle": [
                    "适度运动，以出汗为宜，如慢跑、游泳",
                    "保持居住环境干燥通风",
                    "避免熬夜，保证充足睡眠"
                ],
                "diet": [
                    "饮食清淡，可适当食用清热祛湿食物，如绿豆、苦瓜、冬瓜等",
                    "避免辛辣、油腻、甜腻食物",
                    "少饮酒，多喝水"
                ],
                "when_to_seek_help": [
                    "如痤疮、口苦等症状明显，建议咨询专业中医师"
                ]
            },
            "血瘀质": {
                "lifestyle": [
                    "适度运动，促进血液循环，如慢跑、太极拳、瑜伽",
                    "保持心情愉悦，避免长期抑郁",
                    "保证充足睡眠"
                ],
                "diet": [
                    "可适当食用活血化瘀食物，如山楂、黑豆、玫瑰花茶等",
                    "避免生冷、寒凉食物",
                    "饮食宜温热"
                ],
                "when_to_seek_help": [
                    "如疼痛、色斑等症状明显，建议咨询专业中医师"
                ]
            },
            "气郁质": {
                "lifestyle": [
                    "保持心情愉悦，多与朋友交流",
                    "适度运动，如散步、瑜伽、听音乐",
                    "培养兴趣爱好，转移注意力",
                    "保证充足睡眠"
                ],
                "diet": [
                    "可适当食用理气食物，如柑橘、玫瑰花茶、薄荷等",
                    "避免过度饮酒和刺激性食物",
                    "饮食规律"
                ],
                "when_to_seek_help": [
                    "如情绪持续低落或出现明显抑郁症状，建议咨询专业心理医生或中医师"
                ]
            },
            "特禀质": {
                "lifestyle": [
                    "避免接触已知的过敏原",
                    "保持居住环境清洁，避免尘螨、花粉等",
                    "适度运动，增强体质，但避免在过敏季节户外运动",
                    "保证充足睡眠"
                ],
                "diet": [
                    "避免食用已知的过敏食物",
                    "饮食清淡，可适当食用抗过敏食物，如红枣、蜂蜜等",
                    "注意观察食物反应"
                ],
                "when_to_seek_help": [
                    "如出现严重过敏反应，应立即就医",
                    "建议咨询专业医生进行过敏原检测"
                ]
            },
        }
        
        return recommendations.get(constitution_type, {
            "lifestyle": ["保持规律作息，适度运动"],
            "diet": ["饮食均衡，避免偏食"],
            "when_to_seek_help": ["如有不适，建议咨询专业医生"]
        })
    
    def get_common_questions(self) -> List[str]:
        """获取需要补充的关键问题"""
        questions = []
        for rule in self.rules.values():
            questions.extend(rule.get("common_questions", []))
        # 去重并返回
        return list(set(questions))[:10]  # 返回前10个不重复的问题


# 全局规则库实例
rulebook = ConstitutionRulebook()
