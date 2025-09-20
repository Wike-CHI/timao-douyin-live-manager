"""
提猫直播助手 - 数据验证工具
包含各种数据验证函数和规则
"""

import re
import json
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime


class ValidationError(Exception):
    """验证错误异常"""
    pass


class Validator:
    """通用验证器基类"""
    
    def __init__(self, required: bool = True, allow_none: bool = False):
        self.required = required
        self.allow_none = allow_none
    
    def validate(self, value: Any, field_name: str = "field") -> Any:
        """验证值"""
        if value is None:
            if self.allow_none:
                return None
            if self.required:
                raise ValidationError(f"{field_name} 是必需的")
            return None
        
        return self._validate_value(value, field_name)
    
    def _validate_value(self, value: Any, field_name: str) -> Any:
        """子类需要实现的验证逻辑"""
        return value


class StringValidator(Validator):
    """字符串验证器"""
    
    def __init__(self, 
                 min_length: int = 0, 
                 max_length: int = None,
                 pattern: str = None,
                 choices: List[str] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
        self.choices = choices
    
    def _validate_value(self, value: Any, field_name: str) -> str:
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} 必须是字符串")
        
        # 长度验证
        if len(value) < self.min_length:
            raise ValidationError(f"{field_name} 长度不能少于 {self.min_length} 个字符")
        
        if self.max_length and len(value) > self.max_length:
            raise ValidationError(f"{field_name} 长度不能超过 {self.max_length} 个字符")
        
        # 正则验证
        if self.pattern and not self.pattern.match(value):
            raise ValidationError(f"{field_name} 格式不正确")
        
        # 选择验证
        if self.choices and value not in self.choices:
            raise ValidationError(f"{field_name} 必须是以下值之一: {', '.join(self.choices)}")
        
        return value


class NumberValidator(Validator):
    """数字验证器"""
    
    def __init__(self, 
                 min_value: Union[int, float] = None,
                 max_value: Union[int, float] = None,
                 integer_only: bool = False,
                 **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.integer_only = integer_only
    
    def _validate_value(self, value: Any, field_name: str) -> Union[int, float]:
        if not isinstance(value, (int, float)):
            try:
                value = float(value)
                if self.integer_only:
                    value = int(value)
            except (ValueError, TypeError):
                raise ValidationError(f"{field_name} 必须是数字")
        
        if self.integer_only and not isinstance(value, int):
            value = int(value)
        
        # 范围验证
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(f"{field_name} 不能小于 {self.min_value}")
        
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(f"{field_name} 不能大于 {self.max_value}")
        
        return value


class ListValidator(Validator):
    """列表验证器"""
    
    def __init__(self, 
                 item_validator: Validator = None,
                 min_length: int = 0,
                 max_length: int = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.item_validator = item_validator
        self.min_length = min_length
        self.max_length = max_length
    
    def _validate_value(self, value: Any, field_name: str) -> List[Any]:
        if not isinstance(value, list):
            raise ValidationError(f"{field_name} 必须是列表")
        
        # 长度验证
        if len(value) < self.min_length:
            raise ValidationError(f"{field_name} 至少需要 {self.min_length} 个元素")
        
        if self.max_length and len(value) > self.max_length:
            raise ValidationError(f"{field_name} 最多只能有 {self.max_length} 个元素")
        
        # 元素验证
        if self.item_validator:
            validated_items = []
            for i, item in enumerate(value):
                try:
                    validated_item = self.item_validator.validate(item, f"{field_name}[{i}]")
                    validated_items.append(validated_item)
                except ValidationError as e:
                    raise ValidationError(f"{field_name}[{i}]: {str(e)}")
            return validated_items
        
        return value


class DictValidator(Validator):
    """字典验证器"""
    
    def __init__(self, 
                 schema: Dict[str, Validator] = None,
                 allow_extra: bool = True,
                 **kwargs):
        super().__init__(**kwargs)
        self.schema = schema or {}
        self.allow_extra = allow_extra
    
    def _validate_value(self, value: Any, field_name: str) -> Dict[str, Any]:
        if not isinstance(value, dict):
            raise ValidationError(f"{field_name} 必须是字典")
        
        validated_data = {}
        
        # 验证已定义的字段
        for key, validator in self.schema.items():
            try:
                validated_data[key] = validator.validate(value.get(key), f"{field_name}.{key}")
            except ValidationError as e:
                raise ValidationError(f"{field_name}.{key}: {str(e)}")
        
        # 处理额外字段
        if self.allow_extra:
            for key, val in value.items():
                if key not in self.schema:
                    validated_data[key] = val
        else:
            extra_keys = set(value.keys()) - set(self.schema.keys())
            if extra_keys:
                raise ValidationError(f"{field_name} 包含不允许的字段: {', '.join(extra_keys)}")
        
        return validated_data


class EmailValidator(StringValidator):
    """邮箱验证器"""
    
    def __init__(self, **kwargs):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        super().__init__(pattern=email_pattern, **kwargs)


class URLValidator(StringValidator):
    """URL验证器"""
    
    def __init__(self, **kwargs):
        url_pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
        super().__init__(pattern=url_pattern, **kwargs)


class DateTimeValidator(Validator):
    """日期时间验证器"""
    
    def __init__(self, 
                 format_str: str = "%Y-%m-%d %H:%M:%S",
                 **kwargs):
        super().__init__(**kwargs)
        self.format_str = format_str
    
    def _validate_value(self, value: Any, field_name: str) -> datetime:
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
            try:
                return datetime.strptime(value, self.format_str)
            except ValueError:
                try:
                    # 尝试ISO格式
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    raise ValidationError(f"{field_name} 日期格式不正确")
        
        raise ValidationError(f"{field_name} 必须是日期时间字符串或datetime对象")


# 预定义验证器实例
required_string = StringValidator(required=True)
optional_string = StringValidator(required=False)
non_empty_string = StringValidator(min_length=1)
email = EmailValidator()
url = URLValidator()
positive_int = NumberValidator(min_value=0, integer_only=True)
positive_float = NumberValidator(min_value=0.0)


def validate_comment(data: Dict[str, Any]) -> Dict[str, Any]:
    """验证评论数据"""
    schema = {
        'user': StringValidator(min_length=1, max_length=50, required=True),
        'content': StringValidator(min_length=1, max_length=500, required=True),
        'timestamp': DateTimeValidator(required=False),
        'platform': StringValidator(choices=['douyin', 'kuaishou', 'bilibili'], required=False),
        'user_level': NumberValidator(min_value=0, max_value=100, integer_only=True, required=False),
        'is_vip': Validator(required=False),
        'gift_count': NumberValidator(min_value=0, integer_only=True, required=False)
    }
    
    validator = DictValidator(schema=schema)
    return validator.validate(data, "comment")


def validate_hot_word(data: Dict[str, Any]) -> Dict[str, Any]:
    """验证热词数据"""
    schema = {
        'word': StringValidator(min_length=1, max_length=50, required=True),
        'count': NumberValidator(min_value=1, integer_only=True, required=True),
        'category': StringValidator(choices=['product', 'emotion', 'question', 'other'], required=False),
        'trend': StringValidator(choices=['up', 'down', 'stable'], required=False),
        'last_updated': DateTimeValidator(required=False)
    }
    
    validator = DictValidator(schema=schema)
    return validator.validate(data, "hot_word")


def validate_ai_script(data: Dict[str, Any]) -> Dict[str, Any]:
    """验证AI话术数据"""
    schema = {
        'content': StringValidator(min_length=1, max_length=200, required=True),
        'type': StringValidator(choices=['welcome', 'product', 'interaction', 'closing', 'question', 'emotion'], required=True),
        'context': ListValidator(item_validator=StringValidator(), required=False),
        'source': StringValidator(choices=['ai', 'template', 'manual'], required=False),
        'score': NumberValidator(min_value=0.0, max_value=10.0, required=False),
        'used': Validator(required=False),
        'created_at': DateTimeValidator(required=False)
    }
    
    validator = DictValidator(schema=schema)
    return validator.validate(data, "ai_script")


def validate_config(data: Dict[str, Any]) -> Dict[str, Any]:
    """验证配置数据"""
    schema = {
        'ai_service': StringValidator(choices=['deepseek', 'openai', 'doubao'], required=False),
        'ai_api_key': StringValidator(min_length=1, required=False),
        'ai_base_url': URLValidator(required=False),
        'ai_model': StringValidator(required=False),
        'max_comments': NumberValidator(min_value=10, max_value=10000, integer_only=True, required=False),
        'hot_word_threshold': NumberValidator(min_value=1, integer_only=True, required=False),
        'script_generation_interval': NumberValidator(min_value=5, integer_only=True, required=False),
        'enable_auto_script': Validator(required=False),
        'log_level': StringValidator(choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], required=False)
    }
    
    validator = DictValidator(schema=schema, allow_extra=True)
    return validator.validate(data, "config")


def validate_api_request(data: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
    """验证API请求数据"""
    schemas = {
        'comments': {
            'limit': NumberValidator(min_value=1, max_value=1000, integer_only=True, required=False),
            'offset': NumberValidator(min_value=0, integer_only=True, required=False),
            'platform': StringValidator(choices=['douyin', 'kuaishou', 'bilibili'], required=False)
        },
        'hot_words': {
            'limit': NumberValidator(min_value=1, max_value=100, integer_only=True, required=False),
            'category': StringValidator(choices=['product', 'emotion', 'question', 'other'], required=False)
        },
        'scripts': {
            'type': StringValidator(choices=['welcome', 'product', 'interaction', 'closing', 'question', 'emotion'], required=False),
            'limit': NumberValidator(min_value=1, max_value=50, integer_only=True, required=False),
            'used': Validator(required=False)
        },
        'config': {
            'key': StringValidator(min_length=1, required=False),
            'value': Validator(required=False)
        }
    }
    
    schema = schemas.get(endpoint, {})
    if not schema:
        return data
    
    validator = DictValidator(schema=schema, allow_extra=True)
    return validator.validate(data, f"{endpoint}_request")


class ValidationResult:
    """验证结果类"""
    
    def __init__(self, is_valid: bool = True, errors: List[str] = None, data: Any = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.data = data
    
    def add_error(self, error: str):
        """添加错误"""
        self.is_valid = False
        self.errors.append(error)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'data': self.data
        }


def validate_with_result(validator: Validator, value: Any, field_name: str = "field") -> ValidationResult:
    """使用验证器验证并返回结果对象"""
    try:
        validated_data = validator.validate(value, field_name)
        return ValidationResult(is_valid=True, data=validated_data)
    except ValidationError as e:
        return ValidationResult(is_valid=False, errors=[str(e)])


def validate_batch(validators: Dict[str, Validator], data: Dict[str, Any]) -> ValidationResult:
    """批量验证"""
    result = ValidationResult(data={})
    
    for field_name, validator in validators.items():
        field_result = validate_with_result(validator, data.get(field_name), field_name)
        
        if field_result.is_valid:
            result.data[field_name] = field_result.data
        else:
            result.is_valid = False
            result.errors.extend(field_result.errors)
    
    return result


def sanitize_input(data: Any) -> Any:
    """清理输入数据"""
    if isinstance(data, str):
        # 移除潜在的恶意字符
        data = data.replace('<', '&lt;').replace('>', '&gt;')
        data = data.replace('&', '&amp;').replace('"', '&quot;')
        data = data.strip()
        return data
    
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    
    return data


def validate_json_schema(data: Any, schema: Dict[str, Any]) -> ValidationResult:
    """使用JSON Schema验证数据"""
    try:
        import jsonschema
        jsonschema.validate(data, schema)
        return ValidationResult(is_valid=True, data=data)
    except ImportError:
        return ValidationResult(is_valid=False, errors=["jsonschema 库未安装"])
    except jsonschema.ValidationError as e:
        return ValidationResult(is_valid=False, errors=[str(e)])


# 常用验证规则
COMMENT_RULES = {
    'user': StringValidator(min_length=1, max_length=50, required=True),
    'content': StringValidator(min_length=1, max_length=500, required=True),
    'timestamp': DateTimeValidator(required=False)
}

HOT_WORD_RULES = {
    'word': StringValidator(min_length=1, max_length=50, required=True),
    'count': NumberValidator(min_value=1, integer_only=True, required=True),
    'category': StringValidator(choices=['product', 'emotion', 'question', 'other'], required=False)
}

AI_SCRIPT_RULES = {
    'content': StringValidator(min_length=1, max_length=200, required=True),
    'type': StringValidator(choices=['welcome', 'product', 'interaction', 'closing', 'question', 'emotion'], required=True),
    'score': NumberValidator(min_value=0.0, max_value=10.0, required=False)
}

CONFIG_RULES = {
    'ai_service': StringValidator(choices=['deepseek', 'openai', 'doubao'], required=False),
    'ai_api_key': StringValidator(min_length=1, required=False),
    'max_comments': NumberValidator(min_value=10, max_value=10000, integer_only=True, required=False)
}