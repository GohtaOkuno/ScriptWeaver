"""
ScriptWeaver変換処理モジュール
.txt/.docx ファイルをHTMLに変換する機能を提供
"""

import re
from pathlib import Path
from typing import List, Optional
from docx import Document


class ScriptConverter:
    """スクリプト変換処理クラス"""
    
    def __init__(self):
        self.css_template = self._load_css_template()
    
    def convert(self, input_file: Path) -> Path:
        """入力ファイルをHTMLに変換"""
        if input_file.suffix.lower() == '.txt':
            content = self._read_text_file(input_file)
        elif input_file.suffix.lower() == '.docx':
            content = self._read_docx_file(input_file)
        else:
            raise ValueError(f"対応していない形式: {input_file.suffix}")
        
        html_content = self._convert_to_html(content)
        output_file = input_file.with_suffix('.html')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_file
    
    def _read_text_file(self, file_path: Path) -> str:
        """テキストファイルを読み込み"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _read_docx_file(self, file_path: Path) -> str:
        """Word文書を読み込み"""
        doc = Document(file_path)
        paragraphs = []
        
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                paragraphs.append(text)
        
        return '\n\n'.join(paragraphs)
    
    def _convert_to_html(self, content: str) -> str:
        """テキストをHTMLに変換"""
        paragraphs = self._split_paragraphs(content)
        html_body = self._process_paragraphs(paragraphs)
        
        html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRPGシナリオ</title>
    <style>
{self.css_template}
    </style>
</head>
<body>
    <div class="container">
{html_body}
    </div>
</body>
</html>"""
        
        return html_template
    
    def _split_paragraphs(self, content: str) -> List[str]:
        """テキストを段落に分割"""
        paragraphs = []
        for paragraph in content.split('\n\n'):
            paragraph = paragraph.strip()
            if paragraph:
                paragraphs.append(paragraph)
        return paragraphs
    
    def _process_paragraphs(self, paragraphs: List[str]) -> str:
        """段落をHTMLに変換"""
        html_parts = []
        
        for paragraph in paragraphs:
            # 見出しの処理（#記号形式）
            if paragraph.startswith('#'):
                html_parts.append(self._convert_heading(paragraph))
            # 番号付き見出しの処理（1. 2-1. 等）
            elif self._is_numbered_heading(paragraph):
                html_parts.append(self._convert_numbered_heading(paragraph))
            # 会話文の処理（「」で囲まれた文）
            elif '「' in paragraph and '」' in paragraph:
                html_parts.append(self._convert_dialogue(paragraph))
            # 通常の段落（CoC6版要素を含む可能性）
            else:
                processed_paragraph = self._process_coc_elements(paragraph)
                html_parts.append(f'        <p>{processed_paragraph}</p>')
        
        return '\n'.join(html_parts)
    
    def _convert_heading(self, paragraph: str) -> str:
        """見出しをHTMLに変換"""
        original_level = 0
        for char in paragraph:
            if char == '#':
                original_level += 1
            else:
                break
        
        level = min(original_level, 6)
        heading_text = paragraph[original_level:].strip()
        return f'        <h{level}>{self._escape_html(heading_text)}</h{level}>'
    
    def _is_numbered_heading(self, paragraph: str) -> bool:
        """番号付き見出しかどうかを判定"""
        # 番号付き見出しのパターン（スペースあり・なし両方対応）
        patterns = [
            r'^\d+\.\s*.+',           # 1. タイトル または 1.タイトル
            r'^\d+-\d+\.\s*.+',       # 1-1. サブタイトル または 1-1.サブタイトル
            r'^\d+-\d+-\d+\.\s*.+',   # 1-1-1. 詳細タイトル または 1-1-1.詳細タイトル
        ]
        
        for pattern in patterns:
            if re.match(pattern, paragraph):
                return True
        return False
    
    def _convert_numbered_heading(self, paragraph: str) -> str:
        """番号付き見出しをHTMLに変換"""
        # 見出しレベルの判定
        level = self._determine_heading_level(paragraph)
        
        # 番号部分を除いてタイトルテキストを抽出
        heading_text = self._extract_heading_text(paragraph)
        
        return f'        <h{level}>{self._escape_html(paragraph)}</h{level}>'
    
    def _determine_heading_level(self, paragraph: str) -> int:
        """番号付き見出しのレベルを判定"""
        if re.match(r'^\d+\.\s*.+', paragraph):
            return 1  # 1. → h1 または 1.xxx → h1
        elif re.match(r'^\d+-\d+\.\s*.+', paragraph):
            return 2  # 1-1. → h2 または 1-1.xxx → h2
        elif re.match(r'^\d+-\d+-\d+\.\s*.+', paragraph):
            return 3  # 1-1-1. → h3 または 1-1-1.xxx → h3
        else:
            return 2  # デフォルト
    
    def _extract_heading_text(self, paragraph: str) -> str:
        """見出しからテキスト部分を抽出"""
        # 番号部分を除去してタイトルのみを取得（スペースあり・なし両方対応）
        match = re.match(r'^[\d\-]+\.\s*(.+)', paragraph)
        if match:
            return match.group(1)
        return paragraph
    
    def _convert_dialogue(self, paragraph: str) -> str:
        """会話文をHTMLに変換"""
        # 「」で囲まれた部分を強調
        dialogue_pattern = r'「([^」]+)」'
        converted = re.sub(
            dialogue_pattern,
            r'<span class="dialogue">「\1」</span>',
            paragraph
        )
        return f'        <p class="dialogue-paragraph">{converted}</p>'
    
    def _escape_html(self, text: str) -> str:
        """HTMLエスケープ処理"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))
    
    def _process_coc_elements(self, text: str) -> str:
        """CoC6版特有要素を処理"""
        # まずHTMLエスケープを実行
        escaped_text = self._escape_html(text)
        
        # エスケープ後のテキストに対してCoC6版変換を適用
        # 優先順位：SAN記法 > ダイス表記 > 技能 > アイテム
        # SAN減少記法の処理（ダイス表記を含むため先に処理）
        escaped_text = self._convert_san_notation_escaped(escaped_text)
        # ダイス表記の処理
        escaped_text = self._convert_dice_notation_escaped(escaped_text)
        # 【技能】記法の処理
        escaped_text = self._convert_skill_notation_escaped(escaped_text)
        # 『アイテム』記法の処理  
        escaped_text = self._convert_item_notation_escaped(escaped_text)
        
        return escaped_text
    
    def _convert_skill_notation(self, text: str) -> str:
        """【技能名】記法をHTMLに変換"""
        pattern = r'【([^】]+)】'
        return re.sub(pattern, r'<span class="coc-skill">【\1】</span>', text)
    
    def _convert_skill_notation_escaped(self, text: str) -> str:
        """【技能名】記法をHTMLに変換（エスケープ済みテキスト用）"""
        pattern = r'【([^】]+)】'
        return re.sub(pattern, r'<span class="coc-skill">【\1】</span>', text)
    
    def _convert_item_notation(self, text: str) -> str:
        """『アイテム名』記法をHTMLに変換"""
        pattern = r'『([^』]+)』'
        return re.sub(pattern, r'<span class="coc-item">『\1』</span>', text)
    
    def _convert_item_notation_escaped(self, text: str) -> str:
        """『アイテム名』記法をHTMLに変換（エスケープ済みテキスト用）"""
        pattern = r'『([^』]+)』'
        return re.sub(pattern, r'<span class="coc-item">『\1』</span>', text)
    
    def _convert_dice_notation(self, text: str) -> str:
        """ダイス表記をHTMLに変換"""
        pattern = r'(\d+d\d+(?:[+\-]\d+)?)'
        return re.sub(pattern, r'<span class="coc-dice">\1</span>', text)
    
    def _convert_dice_notation_escaped(self, text: str) -> str:
        """ダイス表記をHTMLに変換（エスケープ済みテキスト用）"""
        pattern = r'(\d+d\d+(?:[+\-]\d+)?)'
        return re.sub(pattern, r'<span class="coc-dice">\1</span>', text)
    
    def _convert_san_notation(self, text: str) -> str:
        """SAN減少記法をHTMLに変換"""
        pattern = r'(SANc?\d+/\d+(?:d\d+)?(?:[+\-]\d+)?)'
        return re.sub(pattern, r'<span class="coc-san">\1</span>', text)
    
    def _convert_san_notation_escaped(self, text: str) -> str:
        """SAN減少記法をHTMLに変換（エスケープ済みテキスト用）"""
        pattern = r'(SANc?\d+/\d+(?:d\d+)?(?:[+\-]\d+)?)'
        return re.sub(pattern, r'<span class="coc-san">\1</span>', text)
    
    def _load_css_template(self) -> str:
        """CSSテンプレートを読み込み"""
        css_path = Path(__file__).parent.parent / 'templates' / 'style.css'
        
        if css_path.exists():
            with open(css_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # デフォルトCSS
            return """        body {
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
        h1 { font-size: 2.2em; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { font-size: 1.8em; border-bottom: 2px solid #3498db; padding-bottom: 8px; }
        h3 { font-size: 1.5em; border-left: 4px solid #3498db; padding-left: 15px; }
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
        }"""