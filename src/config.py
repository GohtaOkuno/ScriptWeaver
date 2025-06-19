"""
設定管理モジュール
ScriptWeaverの全体設定を集約管理
"""

from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class ScriptWeaverConfig:
    """ScriptWeaver全体設定"""
    
    # ファイル処理設定
    default_encoding: str = 'utf-8'
    supported_encodings: List[str] = field(default_factory=lambda: [
        'utf-8', 'shift_jis', 'cp932', 'euc-jp', 'iso-2022-jp'
    ])
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    encoding_detection_sample_size: int = 100000  # 100KB
    encoding_confidence_threshold: float = 0.7
    
    # HTML生成設定
    html_title: str = 'TRPGシナリオ'
    css_template_path: Optional[Path] = None
    include_toc: bool = True
    toc_title: str = '目次'
    
    # バリデーション設定
    enable_validation: bool = False
    strict_mode: bool = False
    trpg_system: str = "CoC6"
    custom_skills: List[str] = field(default_factory=list)
    warning_threshold: int = 10
    auto_fix: bool = True
    beginner_mode: bool = False
    
    # パフォーマンス設定
    regex_cache_size: int = 256
    heading_id_cache_size: int = 256
    enable_chardet: bool = True
    
    # 出力設定
    output_suffix: str = '.html'
    preserve_original: bool = True
    
    def __post_init__(self):
        """初期化後の処理"""
        # CSSテンプレートパスのデフォルト設定
        if self.css_template_path is None:
            self.css_template_path = Path(__file__).parent.parent / 'templates' / 'style.css'
    
    def get_validation_config(self):
        """バリデーション用設定を取得"""
        from .validation import ValidationConfig
        return ValidationConfig(
            strict_mode=self.strict_mode,
            trpg_system=self.trpg_system,
            custom_skills=self.custom_skills,
            warning_threshold=self.warning_threshold,
            auto_fix=self.auto_fix,
            beginner_mode=self.beginner_mode
        )
    
    def load_css_template(self) -> str:
        """CSSテンプレートを読み込み"""
        if self.css_template_path and self.css_template_path.exists():
            try:
                with open(self.css_template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                pass
        
        # フォールバック用の基本CSS
        return self._get_fallback_css()
    
    def _get_fallback_css(self) -> str:
        """フォールバック用の基本CSS"""
        return """
        body {
            font-family: "Noto Sans JP", "Hiragino Kaku Gothic ProN", "Meiryo", sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f9f9f9;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1, h2, h3, h4, h5, h6 {
            color: #2c3e50;
            margin-top: 2em;
            margin-bottom: 1em;
        }
        h1 { 
            font-size: 2.2em; 
            border-bottom: 3px solid #3498db; 
            padding-bottom: 10px; 
        }
        h2 { 
            font-size: 1.8em; 
            border-bottom: 2px solid #3498db; 
            padding-bottom: 8px; 
        }
        h3 { 
            font-size: 1.5em; 
            border-left: 4px solid #3498db; 
            padding-left: 15px; 
        }
        p {
            margin-bottom: 1.5em;
            text-align: justify;
        }
        .dialogue {
            font-style: italic;
            color: #e74c3c;
            font-weight: bold;
        }
        .dialogue-paragraph {
            background-color: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #e74c3c;
            margin: 20px 0;
        }
        .coc-skill {
            color: #2980b9;
            font-weight: bold;
            background-color: #ebf3fd;
            padding: 2px 6px;
            border-radius: 4px;
        }
        .coc-item {
            color: #27ae60;
            font-style: italic;
            background-color: #eafaf1;
            padding: 2px 6px;
            border-radius: 4px;
        }
        .coc-dice {
            color: #e74c3c;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-weight: bold;
            background-color: #fdf2f2;
            padding: 2px 6px;
            border-radius: 4px;
        }
        .coc-san {
            color: #8e44ad;
            font-weight: bold;
            background-color: #f8f4fd;
            padding: 2px 6px;
            border-radius: 4px;
        }
        """
    
    @classmethod
    def create_default(cls) -> 'ScriptWeaverConfig':
        """デフォルト設定を作成"""
        return cls()
    
    @classmethod
    def create_beginner_mode(cls) -> 'ScriptWeaverConfig':
        """初心者向け設定を作成"""
        return cls(
            beginner_mode=True,
            strict_mode=False,
            warning_threshold=20,
            auto_fix=True
        )
    
    @classmethod
    def create_strict_mode(cls) -> 'ScriptWeaverConfig':
        """厳密モード設定を作成"""
        return cls(
            strict_mode=True,
            warning_threshold=5,
            auto_fix=False,
            beginner_mode=False
        )