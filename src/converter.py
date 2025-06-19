"""
ScriptWeaver変換処理モジュール
.txt/.docx ファイルをHTMLに変換する機能を提供

リファクタリング版: 内部的に新しい設計を使用しつつ、既存APIとの互換性を保持
"""

from pathlib import Path
from typing import Optional

# リファクタリングされたクラスをインポート
from .config import ScriptWeaverConfig
from .converter_refactored import ScriptConverter as RefactoredScriptConverter


class ScriptConverter:
    """
    ScriptWeaver変換処理クラス（互換性維持版）
    
    内部的にはリファクタリングされたクラスを使用しながら、
    既存のAPIとの互換性を保持するラッパークラス
    """
    
    def __init__(self, enable_validation: bool = False):
        """
        初期化（既存APIとの互換性維持）
        
        Args:
            enable_validation: バリデーション有効化フラグ
        """
        # 設定を作成
        self.config = ScriptWeaverConfig.create_default()
        self.config.enable_validation = enable_validation
        
        # リファクタリングされたコンバータを内部で使用
        self._converter = RefactoredScriptConverter(self.config)
        
        # 互換性のためのプロパティ
        self.css_template = self.config.load_css_template()
        self.enable_validation = enable_validation
        self.validation_engine = self._converter.validation_engine
    
    def convert(self, input_file: Path, include_validation_report: bool = False) -> Path:
        """
        入力ファイルをHTMLに変換（既存APIとの互換性維持）
        
        Args:
            input_file: 変換対象ファイル
            include_validation_report: バリデーションレポートを含めるか
            
        Returns:
            Path: 生成されたHTMLファイルのパス
        """
        return self._converter.convert(input_file, include_validation_report)
    
    def validate_only(self, input_file: Path):
        """
        バリデーションのみ実行（既存APIとの互換性維持）
        
        Args:
            input_file: 検証対象ファイル
            
        Returns:
            ValidationReport: バリデーション結果
        """
        return self._converter.validate_only(input_file)
    
    # 以下、既存のprivateメソッドとの互換性維持のため、
    # 新しい専門クラスへのプロキシメソッドを提供
    
    def _read_text_file(self, file_path: Path) -> str:
        """テキストファイル読み込み（互換性維持）"""
        return self._converter.file_reader._read_text_file(file_path)
    
    def _read_docx_file(self, file_path: Path) -> str:
        """Word文書読み込み（互換性維持）"""
        return self._converter.file_reader._read_docx_file(file_path)
    
    def _convert_to_html(self, content: str, validation_report=None) -> str:
        """HTML変換（互換性維持）"""
        paragraphs = self._converter.content_processor.split_paragraphs(content)
        headings = self._converter.content_processor.collect_headings(paragraphs)
        
        return self._converter.html_generator.generate_html(
            paragraphs, 
            headings, 
            self._converter.content_processor,
            validation_report
        )
    
    def _split_paragraphs(self, content: str) -> list[str]:
        """段落分割（互換性維持）"""
        return self._converter.content_processor.split_paragraphs(content)
    
    def _collect_headings(self, paragraphs: list[str]) -> list[dict]:
        """見出し収集（互換性維持）"""
        return self._converter.content_processor.collect_headings(paragraphs)
    
    def _process_paragraphs(self, paragraphs: list[str], headings: list[dict] = None) -> str:
        """段落処理（互換性維持）"""
        return self._converter.html_generator._process_paragraphs(
            paragraphs, headings or [], self._converter.content_processor
        )
    
    def _convert_heading(self, paragraph: str, heading_ids: dict = None) -> str:
        """見出し変換（互換性維持）"""
        return self._converter.html_generator._convert_heading(paragraph, heading_ids)
    
    def _convert_dialogue(self, paragraph: str) -> str:
        """会話文変換（互換性維持）"""
        return self._converter.html_generator._convert_dialogue(
            paragraph, self._converter.content_processor
        )
    
    def _escape_html(self, text: str) -> str:
        """HTMLエスケープ（互換性維持）"""
        return self._converter.content_processor._escape_html(text)
    
    def _process_coc_elements(self, text: str) -> str:
        """CoC6版要素処理（互換性維持）"""
        return self._converter.content_processor.process_coc_elements(text)
    
    def _convert_skill_notation(self, text: str) -> str:
        """技能記法変換（互換性維持）"""
        return self._converter.content_processor._convert_skill_notation(text)
    
    def _convert_item_notation(self, text: str) -> str:
        """アイテム記法変換（互換性維持）"""
        return self._converter.content_processor._convert_item_notation(text)
    
    def _convert_dice_notation(self, text: str) -> str:
        """ダイス記法変換（互換性維持）"""
        return self._converter.content_processor._convert_dice_notation(text)
    
    def _convert_san_notation(self, text: str) -> str:
        """SAN記法変換（互換性維持）"""
        return self._converter.content_processor._convert_san_notation(text)
    
    def _is_table(self, paragraph: str) -> bool:
        """表判定（互換性維持）"""
        return self._converter.content_processor.is_table(paragraph)
    
    def _convert_table(self, paragraph: str) -> str:
        """表変換（互換性維持）"""
        return self._converter.html_generator._convert_table(
            paragraph, self._converter.content_processor
        )
    
    def _is_numbered_heading(self, paragraph: str) -> bool:
        """番号付き見出し判定（互換性維持）"""
        return self._converter.content_processor._is_numbered_heading(paragraph)
    
    def _convert_numbered_heading(self, paragraph: str, heading_ids: dict = None) -> str:
        """番号付き見出し変換（互換性維持）"""
        return self._converter.html_generator._convert_numbered_heading(paragraph, heading_ids)
    
    def _determine_heading_level(self, paragraph: str) -> int:
        """見出しレベル判定（互換性維持）"""
        return self._converter.content_processor._determine_heading_level(paragraph)
    
    def _extract_heading_text(self, paragraph: str) -> str:
        """見出しテキスト抽出（互換性維持）"""
        # 簡略実装
        import re
        match = re.match(r'^[\d\-]+\.\s*(.+)', paragraph)
        if match:
            return match.group(1)
        return paragraph
    
    def _is_section_divider(self, paragraph: str) -> bool:
        """セクション区切り判定（互換性維持）"""
        return self._converter.content_processor.is_section_divider(paragraph)
    
    def _convert_section_divider(self, paragraph: str) -> str:
        """セクション区切り変換（互換性維持）"""
        return self._converter.html_generator._convert_section_divider(
            paragraph, self._converter.content_processor
        )
    
    def _is_definition_list(self, paragraph: str) -> bool:
        """定義リスト判定（互換性維持）"""
        return self._converter.content_processor.is_definition_list(paragraph)
    
    def _convert_definition_list(self, paragraph: str) -> str:
        """定義リスト変換（互換性維持）"""
        return self._converter.html_generator._convert_definition_list(
            paragraph, self._converter.content_processor
        )
    
    def _is_bullet_list(self, paragraph: str) -> bool:
        """箇条書き判定（互換性維持）"""
        return self._converter.content_processor.is_bullet_list(paragraph)
    
    def _convert_bullet_list(self, paragraph: str) -> str:
        """箇条書き変換（互換性維持）"""
        return self._converter.html_generator._convert_bullet_list(
            paragraph, self._converter.content_processor
        )
    
    def _is_npc_status(self, paragraph: str) -> bool:
        """NPCステータス判定（互換性維持）"""
        return self._converter.content_processor.is_npc_status(paragraph)
    
    def _convert_npc_status(self, paragraph: str) -> str:
        """NPCステータス変換（互換性維持）"""
        return self._converter.html_generator._convert_npc_status(
            paragraph, self._converter.content_processor
        )
    
    def _generate_toc(self, headings: list[dict]) -> str:
        """目次生成（互換性維持）"""
        return self._converter.html_generator._generate_toc(headings)
    
    def _generate_heading_id(self, text: str) -> str:
        """見出しID生成（互換性維持）"""
        return self._converter.content_processor._generate_heading_id(text)
    
    def _generate_validation_html(self, validation_report) -> str:
        """バリデーションHTML生成（互換性維持）"""
        return self._converter.html_generator._generate_validation_html(validation_report)
    
    def _load_css_template(self) -> str:
        """CSSテンプレート読み込み（互換性維持）"""
        return self.config.load_css_template()
    
    # 新しい機能へのアクセス
    
    def get_config(self) -> ScriptWeaverConfig:
        """設定オブジェクトを取得"""
        return self.config
    
    def update_config(self, **kwargs):
        """設定を更新"""
        self._converter.update_config(**kwargs)
        # 変更された設定を反映
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        # プロパティも更新
        self.enable_validation = self.config.enable_validation
        self.validation_engine = self._converter.validation_engine
    
    def get_supported_formats(self) -> list[str]:
        """サポート形式の取得"""
        return self._converter.get_supported_formats()