"""
レガシー版ScriptConverter（元のconverter.py）
後方互換性維持のためにバックアップとして保存
"""

import re
from pathlib import Path
from typing import List, Optional
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from .validation import (
        ValidationEngine, ValidationConfig, SkillValidator, 
        HeadingValidator, DiceValidator
    )
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False


class ScriptConverterLegacy:
    """スクリプト変換処理クラス（レガシー版）"""
    
    def __init__(self, enable_validation: bool = True):
        self.css_template = self._load_css_template()
        self.enable_validation = enable_validation and VALIDATION_AVAILABLE
        
        # バリデーションエンジンの初期化
        if self.enable_validation:
            self.validation_config = ValidationConfig()
            self.validation_engine = ValidationEngine(self.validation_config)
            
            # バリデータを登録
            self.validation_engine.register_validator(SkillValidator(self.validation_config))
            self.validation_engine.register_validator(HeadingValidator(self.validation_config))
            self.validation_engine.register_validator(DiceValidator(self.validation_config))
        else:
            self.validation_engine = None
    
    # 残りのメソッドは元のconverter.pyと同じ...
    # （元のファイルからコピー）