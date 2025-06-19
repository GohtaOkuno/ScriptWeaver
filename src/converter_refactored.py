"""
リファクタリングされたScriptConverter
責任分離とパフォーマンス改善を実装
"""

from pathlib import Path
from typing import Optional

from .config import ScriptWeaverConfig
from .file_reader import FileReader
from .content_processor import ContentProcessor
from .html_generator import HTMLGenerator

try:
    from .validation import ValidationEngine
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False


class ScriptConverter:
    """
    リファクタリングされたメインコントローラークラス
    各専門クラスのオーケストレーションを担当
    """
    
    def __init__(self, config: Optional[ScriptWeaverConfig] = None):
        """
        初期化
        
        Args:
            config: ScriptWeaverの設定オブジェクト
        """
        self.config = config or ScriptWeaverConfig.create_default()
        
        # 各専門クラスを初期化
        self.file_reader = FileReader()
        self.content_processor = ContentProcessor()
        self.html_generator = HTMLGenerator(self.config.load_css_template())
        
        # バリデーションエンジンの初期化
        self.validation_engine = None
        if self.config.enable_validation and VALIDATION_AVAILABLE:
            self._initialize_validation_engine()
    
    def _initialize_validation_engine(self):
        """バリデーションエンジンを初期化"""
        from .validation import SkillValidator, HeadingValidator, DiceValidator
        
        validation_config = self.config.get_validation_config()
        self.validation_engine = ValidationEngine(validation_config)
        
        # 標準バリデータを登録
        self.validation_engine.register_validator(SkillValidator(validation_config))
        self.validation_engine.register_validator(HeadingValidator(validation_config))
        self.validation_engine.register_validator(DiceValidator(validation_config))
    
    def convert(self, input_file: Path, include_validation_report: bool = False) -> Path:
        """
        入力ファイルをHTMLに変換
        
        Args:
            input_file: 変換対象ファイル(.txt/.docx)
            include_validation_report: バリデーションレポートをHTMLに含めるか
            
        Returns:
            Path: 生成されたHTMLファイルのパス
            
        Raises:
            ValueError: 対応していないファイル形式の場合
            IOError: ファイル読み込みに失敗した場合
        """
        # ファイルサポート確認
        if not self.file_reader.is_supported_file(input_file):
            raise ValueError(f"対応していない形式: {input_file.suffix}")
        
        # ファイル読み込み
        content = self.file_reader.read_file(input_file)
        
        # バリデーション実行（オプション）
        validation_report = None
        if self.validation_engine and include_validation_report:
            validation_report = self.validation_engine.validate_document(content)
            
            # 厳密モードで重大エラーがある場合は変換を停止
            if self.config.strict_mode and validation_report.has_errors():
                raise ValueError(
                    f"バリデーションで重大エラーが検出されました。"
                    f"重大エラー数: {validation_report.summary['critical']}"
                )
        
        # コンテンツ処理
        paragraphs = self.content_processor.split_paragraphs(content)
        headings = self.content_processor.collect_headings(paragraphs)
        
        # HTML生成
        html_content = self.html_generator.generate_html(
            paragraphs, 
            headings, 
            self.content_processor,
            validation_report if include_validation_report else None
        )
        
        # 出力ファイル作成
        output_file = input_file.with_suffix(self.config.output_suffix)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
        except Exception as e:
            raise IOError(f"HTMLファイルの書き込みに失敗しました: {output_file}\nエラー: {e}")
        
        return output_file
    
    def validate_only(self, input_file: Path):
        """
        バリデーションのみ実行（変換はしない）
        
        Args:
            input_file: 検証対象ファイル
            
        Returns:
            ValidationReport: バリデーション結果
            
        Raises:
            RuntimeError: バリデーション機能が無効化されている場合
            ValueError: 対応していないファイル形式の場合
        """
        if not self.validation_engine:
            raise RuntimeError("バリデーション機能が無効化されています")
        
        if not self.file_reader.is_supported_file(input_file):
            raise ValueError(f"対応していない形式: {input_file.suffix}")
        
        content = self.file_reader.read_file(input_file)
        return self.validation_engine.validate_document(content)
    
    def get_supported_formats(self) -> list[str]:
        """サポートしているファイル形式のリストを取得"""
        return self.file_reader.get_supported_extensions()
    
    def get_config(self) -> ScriptWeaverConfig:
        """現在の設定を取得"""
        return self.config
    
    def update_config(self, **kwargs):
        """設定を更新"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        # バリデーション設定が変更された場合は再初期化
        validation_keys = {
            'enable_validation', 'strict_mode', 'trpg_system', 
            'custom_skills', 'warning_threshold', 'auto_fix', 'beginner_mode'
        }
        if any(key in validation_keys for key in kwargs.keys()):
            if self.config.enable_validation and VALIDATION_AVAILABLE:
                self._initialize_validation_engine()
            else:
                self.validation_engine = None


# 後方互換性のための関数群
def create_converter(enable_validation: bool = True) -> ScriptConverter:
    """
    旧APIとの互換性のためのファクトリ関数
    
    Args:
        enable_validation: バリデーション有効化フラグ
        
    Returns:
        ScriptConverter: 設定済みのコンバータインスタンス
    """
    config = ScriptWeaverConfig.create_default()
    config.enable_validation = enable_validation
    return ScriptConverter(config)


def create_beginner_converter() -> ScriptConverter:
    """初心者向けコンバータを作成"""
    config = ScriptWeaverConfig.create_beginner_mode()
    return ScriptConverter(config)


def create_strict_converter() -> ScriptConverter:
    """厳密モードコンバータを作成"""
    config = ScriptWeaverConfig.create_strict_mode()
    return ScriptConverter(config)