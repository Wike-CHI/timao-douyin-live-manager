# -*- coding: utf-8 -*-
"""
Gemini AI 增强适配器 - 专注于"颜值暧昧"类直播的内容质量复盘

在原有 gemini_adapter.py 基础上增强，重点分析：
1. 话题抽取与时间序列分析
2. 触发点识别（消费/关注/互动的触发话题）
3. 高价值用户识别与运营建议
4. 可复制话术与训练要点
"""

import json
import logging
from typing import Dict, Any, List, Optional
from .gemini_adapter import GeminiAdapter, get_gemini_adapter, _generate_real_trend_charts

logger = logging.getLogger(__name__)


def _split_transcript_into_time_windows(
    transcript_data,
    duration_seconds: int,
    window_size: int = 30
) -> List[Dict[str, Any]]:
    """将转写按时间窗切分，支持精确定位
    
    Args:
        transcript_data: 带时间戳的分段列表或纯文本字符串
        duration_seconds: 直播总时长
        window_size: 时间窗大小（秒），默认30秒
    
    Returns:
        时间窗列表，每个窗口包含 start_time, end_time, text
    """
    windows = []
    
    # 情况1：带时间戳的分段数据（推荐）
    if isinstance(transcript_data, list) and transcript_data:
        for segment in transcript_data:
            seg_start = segment.get("start_time", 0)
            seg_end = segment.get("end_time", seg_start + 1800)
            seg_text = segment.get("text", "")
            
            if not seg_text.strip():
                continue
            
            # 按句子切分（中文句号、问号、感叹号）
            import re
            sentences = re.split(r'[。！？\n]+', seg_text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                continue
            
            # 计算分段时长
            seg_duration = seg_end - seg_start
            
            # 将句子均匀分布到时间段内
            num_sentences = len(sentences)
            avg_sentence_duration = seg_duration / num_sentences if num_sentences > 0 else seg_duration
            
            current_time = seg_start
            current_window_text = []
            window_start = current_time
            
            for i, sentence in enumerate(sentences):
                sentence_end = current_time + avg_sentence_duration
                current_window_text.append(sentence)
                
                # 当累积到30秒或最后一句时，保存窗口
                if (sentence_end - window_start >= window_size) or (i == num_sentences - 1):
                    windows.append({
                        "start_time": int(window_start),
                        "end_time": int(min(sentence_end, seg_end)),
                        "text": "。".join(current_window_text) + "。"
                    })
                    current_window_text = []
                    window_start = sentence_end
                
                current_time = sentence_end
    
    # 情况2：纯文本（降级方案）
    elif isinstance(transcript_data, str):
        # 简单按字符数均匀切分
        text = transcript_data
        total_chars = len(text)
        if total_chars == 0:
            return windows
        
        chars_per_second = total_chars / duration_seconds if duration_seconds > 0 else total_chars
        window_chars = int(chars_per_second * window_size)
        
        current_pos = 0
        current_time = 0
        
        while current_pos < total_chars:
            end_pos = min(current_pos + window_chars, total_chars)
            window_text = text[current_pos:end_pos].strip()
            
            if window_text:
                windows.append({
                    "start_time": current_time,
                    "end_time": current_time + window_size,
                    "text": window_text
                })
            
            current_pos = end_pos
            current_time += window_size
    
    return windows


def _format_seconds(seconds: int) -> str:
    """格式化秒数为 MM:SS 或 HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def _match_events_to_time_windows(
    events: List[Dict],
    windows: List[Dict],
    time_window_seconds: int = 30
) -> Dict[str, List[Dict]]:
    """将事件（礼物/关注）匹配到对应的时间窗
    
    Args:
        events: 事件列表（包含 timestamp 字段，毫秒）
        windows: 时间窗列表
        time_window_seconds: 匹配窗口大小（秒）
    
    Returns:
        匹配结果字典
    """
    matched = {}
    
    for event in events:
        timestamp_ms = event.get("timestamp", 0)
        if not timestamp_ms:
            continue
        
        # 转换为秒
        event_time = timestamp_ms / 1000 if timestamp_ms > 1e10 else timestamp_ms
        
        # 查找前后30秒内的时间窗
        for window in windows:
            window_start = window["start_time"]
            window_end = window["end_time"]
            
            # 事件在窗口内或窗口的±30秒范围内
            if (window_start - time_window_seconds <= event_time <= window_end + time_window_seconds):
                window_key = f"{window_start}-{window_end}"
                if window_key not in matched:
                    matched[window_key] = {
                        "window": window,
                        "events": []
                    }
                matched[window_key]["events"].append(event)
    
    return matched


def _analyze_comment_events(comments: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """分析弹幕事件，分类为聊天、礼物、关注等
    
    Args:
        comments: 弹幕列表
    
    Returns:
        分类后的事件字典
    """
    gift_events = []
    follow_events = []
    chat_comments = []
    like_events = []
    entry_events = []
    
    for comment in comments:
        if not isinstance(comment, dict):
            continue
            
        event_type = comment.get("type", "comment")
        
        # 礼物事件
        if event_type == "gift" or "gift" in comment or "gift_name" in comment:
            gift_events.append(comment)
        # 关注事件
        elif event_type in ["follow", "social"]:
            follow_events.append(comment)
        # 点赞事件
        elif event_type == "like":
            like_events.append(comment)
        # 进场事件
        elif event_type in ["member", "entry"]:
            entry_events.append(comment)
        # 普通弹幕
        else:
            chat_comments.append(comment)
    
    return {
        "gifts": gift_events,
        "follows": follow_events,
        "chats": chat_comments,
        "likes": like_events,
        "entries": entry_events
    }


def _build_content_analysis_prompt(
    anchor_name: str,
    duration_seconds: int,
    transcript_data,  # 🔄 支持 List[Dict] 或 str
    events: Dict[str, List],
    metrics: Dict[str, Any]
) -> str:
    """构建专注于内容质量的分析提示词
    
    Args:
        anchor_name: 主播名称
        duration_seconds: 直播时长
        transcript_data: 带时间戳的分段列表或纯文本
        events: 分类后的事件
        metrics: 直播数据
    
    Returns:
        完整的提示词
    """
    duration_minutes = duration_seconds // 60
    
    # 🆕 将转写切分为时间窗（每30秒）
    time_windows = _split_transcript_into_time_windows(
        transcript_data, 
        duration_seconds, 
        window_size=30
    )
    
    logger.info(f"📊 转写切分完成 - {len(time_windows)} 个时间窗（每30秒）")
    
    # 🆕 匹配礼物和关注事件到时间窗
    gift_matches = _match_events_to_time_windows(events["gifts"], time_windows, time_window_seconds=30)
    follow_matches = _match_events_to_time_windows(events["follows"], time_windows, time_window_seconds=30)
    
    logger.info(
        f"🎯 事件匹配完成 - 礼物触发点: {len(gift_matches)}, 关注触发点: {len(follow_matches)}"
    )
    
    # 🆕 格式化带时间戳的转写文本（限制展示数量）
    max_windows_to_show = min(100, len(time_windows))  # 最多展示100个窗口
    transcript_with_timestamps = "\n\n".join([
        f"[{_format_seconds(w['start_time'])} - {_format_seconds(w['end_time'])}]\n{w['text']}"
        for w in time_windows[:max_windows_to_show]
    ])
    
    if len(time_windows) > max_windows_to_show:
        transcript_with_timestamps += f"\n\n...（省略 {len(time_windows) - max_windows_to_show} 个时间窗）"
    
    # 🆕 格式化触发点证据（展示匹配到事件的时间窗）
    trigger_evidence = []
    
    # 礼物触发点
    for window_key, match_data in list(gift_matches.items())[:10]:  # 最多展示10个
        window = match_data["window"]
        events_list = match_data["events"]
        trigger_evidence.append({
            "type": "gift",
            "time": f"{_format_seconds(window['start_time'])} - {_format_seconds(window['end_time'])}",
            "transcript": window["text"][:200],  # 截取前200字
            "events": [
                {
                    "user": e.get("user", "未知"),
                    "gift": e.get("gift_name", e.get("gift", "未知礼物")),
                    "count": e.get("count", 1)
                }
                for e in events_list[:5]  # 最多展示5个事件
            ]
        })
    
    # 关注触发点
    for window_key, match_data in list(follow_matches.items())[:10]:
        window = match_data["window"]
        events_list = match_data["events"]
        trigger_evidence.append({
            "type": "follow",
            "time": f"{_format_seconds(window['start_time'])} - {_format_seconds(window['end_time'])}",
            "transcript": window["text"][:200],
            "events": [
                {"user": e.get("user", "未知")}
                for e in events_list[:5]
            ]
        })
    
    # 限制弹幕和事件数量
    chat_preview = events["chats"][:200] if len(events["chats"]) > 200 else events["chats"]
    
    prompt = f"""你是一个专注于**颜值暧昧类主播**的直播复盘教练。你的目标是帮助主播提升内容质量，识别优质话术，训练消费刺激能力，并指导大哥维护策略。

## 🎯 核心任务（按优先级排序）

### 1️⃣ 话题质量分析（最重要）
**目标**: 识别本场主播和观众讨论的话题，评估内容质量，给出延伸建议

**分析方法**:
- 主播话题：从语音转写中识别主播主动抛出的话题
- 观众话题：从弹幕中识别观众反复提及的话题
- 质量评分：根据弹幕互动量、情绪饱满度、话题延续时间评分

**输出要求**:
- 列出主播主动抛出的话题（3-8个），每个包含：
  - 时间区间（MM:SS - MM:SS）
  - 关键台词（原文引用）
  - 内容质量评分（1-5分，1=冷场，5=高互动）
  - 评分理由
  - **话题延伸建议**（2-3个具体延伸方向）
  - 情绪标签

- 列出观众主动抛出的话题（3-5个），每个包含：
  - 典型弹幕样本
  - 主播如何回应（评价）
  - **改进建议**（话术示例）

### 2️⃣ 消费刺激分析（第二重要）
**目标**: 精确识别哪些话术/话题触发了礼物消费

**分析方法**:
- 对每个礼物事件，查找前后30秒的主播话术
- 置信度 ≥ 0.7 才输出

**输出要求**:
- 列出2-5个消费触发点，每个包含：
  - 触发话题（简短概括）
  - 证据（时间+话术+礼物列表）
  - 置信度（0.7-1.0）
  - **深度分析**（为什么有效？）
  - **训练建议**（3个训练要点）

### 3️⃣ 大哥维护策略（运营核心）
**目标**: 识别高价值用户，给出后续跟进建议

**输出要求**:
- 列出3-5个高价值用户，每个包含：
  - 用户昵称、贡献统计
  - **互动上下文分析**（活跃时段+话题+弹幕+主播回应）
  - **跟进建议**（私聊话术+专属权益+时间节点）

### 4️⃣ 可复制话术库（训练卡片）
**目标**: 提取3-5个可直接复制使用的话术模板

### 5️⃣ 训练要点（明日改进清单）
**目标**: 给出3-5个具体训练任务

---

## � 输入数据

### 基础信息
- 主播: {anchor_name}
- 直播时长: {_format_seconds(duration_seconds)}

### 语音转写（带30秒时间窗）
{transcript_with_timestamps}

### 弹幕消息样本（前50条）
{json.dumps(chat_preview[:50], ensure_ascii=False, indent=2)}

### 礼物记录（完整列表）
{json.dumps(trigger_evidence, ensure_ascii=False, indent=2)}

### 数据指标参考（仅供参考）
- 总弹幕数: {len(events['chats'])}
- 总礼物数: {len(events['gifts'])}
- 总关注数: {len(events['follows'])}

---

## 📤 输出JSON格式：

{{
  "content_topics": {{
    "anchor_topics": [
      {{
        "topic": "话题名称（如：颜值互动）",
        "time_range": "05:30 - 08:00",
        "key_quotes": ["主播说的原话1", "主播说的原话2"],
        "quality_score": 4.2,
        "quality_reason": "情绪饱满，观众互动热烈，但话题延伸不够深入",
        "extension_suggestions": [
          "可以让观众猜主播年龄/星座，增加悬念和互动",
          "可以分享保养秘诀，建立专业人设",
          "可以询问观众喜欢什么类型，制造暧昧氛围"
        ],
        "emotion_tags": ["撒娇", "暧昧"]
      }}
    ],
    "audience_topics": [
      {{
        "topic": "求加微信",
        "sample_comments": ["加个微信吧", "有私人号吗", "怎么联系你"],
        "anchor_response": "主播简单回复'关注就可以联系'，但未深入互动",
        "improvement_suggestions": [
          "话术示例：'宝宝们想加微信呀？那先关注我，私信暗号【小心心】，我看到会回哦~'",
          "技巧：制造稀缺感+明确行动指令，提升关注转化"
        ]
      }}
    ],
    "top_keywords": ["漂亮", "加微信", "唱歌", "可爱", "关注"]
  }},
  
  "trigger_analysis": {{
    "consumption_triggers": [
      {{
        "topic": "撒娇求礼物",
        "evidence": {{
          "time": "12:30 - 13:00",
          "transcript_quote": "哥哥们，今天没人给我刷礼物吗？好伤心哦~",
          "gifts": [
            {{"user": "用户A", "gift": "小心心", "count": 5, "value": 5}},
            {{"user": "用户B", "gift": "玫瑰花", "count": 10, "value": 10}}
          ],
          "related_comments": ["来了来了", "给姐姐刷"]
        }},
        "confidence": 0.92,
        "deep_analysis": "使用撒娇语气+可怜情绪，配合'今天没人'制造稀缺感和紧迫感，触发用户保护欲和补偿心理。语调降低、语速放慢，增强情感共鸣。",
        "training_tips": [
          "语气训练：降低音调、拖长尾音，模拟委屈状态（如：'好伤心哦~~~'）",
          "时机把握：在观众活跃但礼物较少时使用，避免过于频繁（建议每30分钟1次）",
          "情绪真实：不要机械重复，每次要有细微变化（如：换成'今天你们都不爱我了吗'）"
        ]
      }}
    ],
    "follow_triggers": [
      {{
        "topic": "福利引导",
        "evidence": {{
          "time": "03:00 - 03:30",
          "transcript_quote": "关注我的宝宝都有惊喜哦，不关注看不到的~",
          "follows": [{{"user": "用户C"}}, {{"user": "用户D"}}],
          "related_comments": ["关注了", "什么惊喜"]
        }},
        "confidence": 0.85,
        "deep_analysis": "明确的价值交换提示（关注=惊喜），制造好奇心和FOMO（害怕错过）心理",
        "training_tips": [
          "话术变化：可替换为'只有关注的宝宝才能看到福利'、'关注我解锁隐藏内容'",
          "兑现承诺：真实提供小福利（如专属表情包、才艺预告），建立信任",
          "频率控制：每场1-2次，避免过度使用降低吸引力"
        ]
      }}
    ],
    "engagement_peaks": [
      {{
        "time_range": "08:00 - 10:00",
        "topic": "才艺展示（唱歌）",
        "chat_count": 45,
        "gift_count": 8,
        "confidence": 0.90,
        "analysis": "唱歌期间弹幕和礼物激增，说明观众喜欢才艺内容，建议增加才艺展示频率"
      }}
    ]
  }},
  
  "high_value_users": [
    {{
      "user_name": "用户A",
      "contribution": {{
        "total_value": 500,
        "gift_count": 20,
        "comment_count": 15,
        "is_followed": true
      }},
      "interaction_context": {{
        "active_topics": ["12:30-13:00 撒娇求礼物", "15:00-16:00 唱歌"],
        "typical_comments": ["姐姐好美", "给你刷礼物", "再唱一首"],
        "anchor_response_quality": "主播每次都点名感谢，但未深入聊天，互动较浅"
      }},
      "follow_up_actions": [
        {{
          "action_type": "私聊话术",
          "timing": "直播结束后1小时内",
          "script": "A哥，今天谢谢你一直支持我呀~ 看到你说【再唱一首】，下次给你点播机会哦。最近工作忙吗？",
          "goal": "建立个人连接，了解对方生活状态，为长期维护打基础"
        }},
        {{
          "action_type": "专属权益",
          "timing": "下次直播前预告",
          "content": "给A哥私人预告：明晚8点有新才艺首秀，只告诉你哦~",
          "goal": "制造VIP特权感，提升忠诚度"
        }},
        {{
          "action_type": "节日问候",
          "timing": "周末或节假日",
          "script": "A哥周末快乐！今天有没有想我呀~（撒娇表情）",
          "goal": "日常维护，保持热度"
        }}
      ]
    }}
  ],
  
  "replicable_scripts": [
    {{
      "scenario": "开场暖场",
      "script": "宝宝们晚上好呀~ 今天【主播心情/状态】，有没有想我呀？来的宝宝扣个【1】让我看到你们~",
      "why_works": "亲切称呼+情感连接+互动指令，快速拉近距离并活跃气氛",
      "usage_tips": "每次开播前3分钟使用，心情/状态可替换（如：好开心、有点累、特别想你们）",
      "evidence": {{
        "time": "00:00 - 00:30",
        "effect": "开场3分钟收获80条弹幕，关注转化率12%"
      }}
    }},
    {{
      "scenario": "礼物感谢（高级版）",
      "script": "谢谢【用户名】的【礼物名】，【用户名】今天这么大方呀~ 是不是发工资了？（调皮）",
      "why_works": "点名感谢+个性化互动+幽默调侃，让用户感到被重视且氛围轻松",
      "usage_tips": "收到大额礼物时使用，避免机械重复'谢谢XX的XX'",
      "evidence": {{
        "time": "12:35 - 12:40",
        "effect": "使用后30秒内触发连续3个礼物"
      }}
    }},
    {{
      "scenario": "冷场救场",
      "script": "宝宝们怎么都不说话了呀？是不是被我美到了？（俏皮）来，活跃的宝宝扣【666】~",
      "why_works": "自嘲+幽默+互动指令，快速打破冷场尴尬",
      "usage_tips": "当弹幕量持续低迷超过2分钟时立即使用",
      "evidence": {{
        "time": "18:00 - 18:30",
        "effect": "冷场后30秒内恢复弹幕20条"
      }}
    }}
  ],
  
  "training_points": [
    {{
      "category": "话术优化",
      "problem": "开场话术单一，前5分钟弹幕量仅20条，低于平均水平30%",
      "action_items": [
        "准备3套开场话术轮换使用（亲切型、搞笑型、撒娇型），避免观众审美疲劳",
        "增加开放式问题（如：'今天有什么开心的事吗？'），引导观众主动发言",
        "设置开场小游戏（如：猜主播今天穿什么颜色），提升参与感"
      ],
      "priority": "高",
      "expected_impact": "预计提升开场5分钟互动率50%，关注转化率提升至15%"
    }},
    {{
      "category": "大哥维护",
      "problem": "本场3个高价值用户未得到充分互动，其中用户A贡献500元但仅被点名感谢2次",
      "action_items": [
        "建立大哥名单，每场直播主动问候Top3用户（如：'A哥今天来啦，么么哒~'）",
        "直播结束后30分钟内私聊Top用户，发送感谢+日常问候（参考上述私聊话术）",
        "每周为大哥准备小惊喜（如：专属表情包、私人定制才艺、节日问候）"
      ],
      "priority": "高",
      "expected_impact": "预计大哥复购率提升30%，月均贡献增加20%"
    }},
    {{
      "category": "情绪表达",
      "problem": "第15-20分钟出现冷场，弹幕量下降60%，主播情绪平淡缺乏起伏",
      "action_items": [
        "学习情绪切换技巧：撒娇→搞笑→暧昧，每10分钟切换一次情绪状态",
        "准备救场话题库（如：分享趣事、才艺展示、互动游戏），冷场时立即使用",
        "观察弹幕情绪，及时调整节奏（弹幕减少=加大互动力度+切换话题）"
      ],
      "priority": "中",
      "expected_impact": "减少50%冷场时间，整体留人率提升10%"
    }},
    {{
      "category": "话题延伸",
      "problem": "颜值互动话题（05:30-08:00）质量评分4.2，但未深入延伸，观众兴趣逐渐下降",
      "action_items": [
        "学习3种话题延伸技巧：反问法（'你们觉得我像谁？'）、悬念法（'下次给你们看素颜照'）、互动法（'帮我选明天的妆容'）",
        "每个话题至少延伸2个子话题，避免浅尝辄止",
        "观看优秀主播视频，学习如何把一个话题聊5-10分钟"
      ],
      "priority": "中",
      "expected_impact": "话题质量评分提升至4.5+，单话题互动时长延长50%"
    }}
  ],
  
  "key_highlights": [
    "撒娇求礼物话术（12:30-13:00）效果显著，30秒内触发15个礼物，建议固定为核心话术",
    "才艺展示（08:00-10:00）互动峰值明显，弹幕+45、礼物+8，建议增加才艺频率",
    "用户A贡献500元成为本场最大哥，已建立良好互动基础，需后续深度维护"
  ],
  
  "key_issues": [
    "开场5分钟互动不足，弹幕量仅20条，需优化开场话术和节奏",
    "第15-20分钟出现明显冷场，弹幕量下降60%，需准备救场话题库",
    "高价值用户维护不足，3个大哥未得到充分互动，错失深度维护机会"
  ],
  
  "improvement_suggestions": [
    "建立话术库系统：开场3套、感谢5套、救场3套、引导关注2套，轮换使用避免重复",
    "制定大哥维护SOP：直播中点名问候→直播后1小时私聊→每周小惊喜→节日祝福",
    "优化直播节奏：开场3分钟暖场→10分钟一次小高潮（才艺/游戏/福利）→避免超过5分钟无互动"
  ],
  
  "notes": "本场数据完整，分析基于完整语音转写和事件记录。建议主播重点关注'消费触发点'和'大哥维护'两个板块，这是提升收入的核心。"
}}

---

## ⚠️ 核心分析要求（必须严格遵守）

### 1. 精确时间引用原则
- ✅ 必须使用语音转写中的具体时间（MM:SS - MM:SS）
- ✅ 必须引用主播话术原文（用引号标注）
- ❌ 不要猜测或编造没有证据的时间点
- ❌ 不要说"大约第X分钟"，要说"05:30 - 06:00"

### 2. 置信度标注原则
- 只输出置信度 ≥ 0.7 的消费/关注触发点
- 如果无法明确关联事件与话术，不要强行输出

### 3. 内容为王原则
- **重点分析内容质量**（话题、话术、情绪），数据只是辅助
- 话题延伸建议必须具体可执行（不说"提升话题质量"，要说"可以让观众猜年龄"）
- 所有结论必须给出"为什么"和"怎么做"

### 4. 可执行原则
- 所有建议必须具体、可落地
- 话术建议要给出完整的话术模板（带【】标注可替换变量）
- 训练建议要给出明确的训练步骤（3条以内）
- 大哥维护要给出完整的跟进流程（话术+时机+目标）

### 5. 质量标准
**优秀复盘的标准**:
- ✅ 每个话题都有具体时间 + 话术原文 + 延伸建议
- ✅ 每个触发点都有证据链（时间→话术→事件→深度分析→训练要点）
- ✅ 大哥维护包含互动上下文分析 + 完整跟进流程
- ✅ 训练要点聚焦3-5个核心问题，不贪多

**避免的错误**:
- ❌ 堆砌数据指标，缺少内容分析
- ❌ 笼统建议（如："提升互动率"），缺少具体动作
- ❌ 无证据的猜测（如："可能是因为...感觉...应该..."）
- ❌ 忽略大哥维护，只关注话术训练

---

现在请基于输入数据进行深度复盘，输出纯JSON（不要markdown标记）："""
    
    return prompt


def generate_enhanced_review_report(review_data: Dict[str, Any]) -> Dict[str, Any]:
    """生成增强版直播复盘报告（专注于内容质量和触发点分析）
    
    Args:
        review_data: 复盘数据（同原版）
    
    Returns:
        增强版复盘报告
    """
    adapter = get_gemini_adapter()
    
    if not adapter.is_available():
        raise RuntimeError("Gemini 服务不可用，请检查 AIHUBMIX_API_KEY 配置")
    
    # 提取数据
    transcript = review_data.get("transcript", "")
    comments = review_data.get("comments", [])
    anchor_name = review_data.get("anchor_name", "主播")
    metrics = review_data.get("metrics", {})
    duration_seconds = int(review_data.get("duration_seconds", 0))
    viewer_snapshots = review_data.get("viewer_snapshots", [])
    
    # 🆕 分析事件
    events = _analyze_comment_events(comments)
    
    logger.info(
        f"📊 数据分类完成 - "
        f"弹幕: {len(events['chats'])}, "
        f"礼物: {len(events['gifts'])}, "
        f"关注: {len(events['follows'])}, "
        f"点赞: {len(events['likes'])}, "
        f"进场: {len(events['entries'])}"
    )
    
    # 🆕 生成趋势图
    trend_charts = _generate_real_trend_charts(metrics, duration_seconds)
    
    # 🆕 构建内容质量分析提示词
    prompt = _build_content_analysis_prompt(
        anchor_name=anchor_name,
        duration_seconds=duration_seconds,
        transcript_data=transcript,  # 🔧 修正参数名
        events=events,
        metrics=metrics
    )
    
    # 调用 Gemini
    logger.info(f"🚀 开始调用 Gemini 生成增强版复盘报告...")
    logger.info(f"📝 转写长度: {len(transcript)} 字符")
    
    result = adapter.generate_review(
        prompt=prompt,
        temperature=0.3,
        max_tokens=6000,  # 增加token限制，支持更详细的分析
        response_format="json"
    )
    
    if not result:
        raise RuntimeError("Gemini API 调用失败")
    
    logger.info(f"✅ Gemini 响应成功 - 长度: {len(result['text'])} 字符")
    
    # 解析 JSON
    report_data = adapter.parse_json_response(result["text"])
    
    if not report_data:
        # 降级方案
        logger.warning("⚠️ JSON解析失败，使用降级方案")
        report_data = {
            "overall_score": 0,
            "performance_analysis": {
                "overall_assessment": "AI分析失败，JSON解析错误",
                "content_quality": {"score": 0, "comments": "解析失败"},
                "engagement": {"score": 0, "comments": "解析失败"},
                "conversion_potential": {"score": 0, "comments": "解析失败"}
            },
            "content_topics": {
                "anchor_topics": [],
                "audience_topics": [],
                "top_keywords": []
            },
            "trigger_analysis": {
                "consumption_triggers": [],
                "follow_triggers": [],
                "engagement_peaks": []
            },
            "high_value_users": [],
            "replicable_scripts": [],
            "training_points": [],
            "key_highlights": ["AI分析遇到问题"],
            "key_issues": ["JSON解析失败"],
            "improvement_suggestions": ["请重试"],
            "error": "JSON解析失败",
            "raw_response_preview": result["text"][:1000]
        }
    
    # 补充元数据
    report_data["ai_model"] = adapter.model
    report_data["generation_cost"] = result["cost"]
    report_data["generation_tokens"] = result["usage"]["total_tokens"]
    report_data["generation_duration"] = result["duration"]
    report_data["trend_charts"] = trend_charts
    
    # 🆕 补充事件统计
    report_data["event_statistics"] = {
        "total_chats": len(events["chats"]),
        "total_gifts": len(events["gifts"]),
        "total_follows": len(events["follows"]),
        "total_likes": len(events["likes"]),
        "total_entries": len(events["entries"])
    }
    
    logger.info(
        f"✅ 增强版复盘完成 - "
        f"评分: {report_data.get('overall_score', 0)}/100, "
        f"成本: ${result['cost']:.6f}, "
        f"耗时: {result['duration']:.2f}s"
    )
    
    return report_data
