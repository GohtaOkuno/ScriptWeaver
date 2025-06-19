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
            # 見出しの処理
            if paragraph.startswith('#'):
                html_parts.append(self._convert_heading(paragraph))
            # 会話文の処理（「」で囲まれた文）
            elif '「' in paragraph and '」' in paragraph:
                html_parts.append(self._convert_dialogue(paragraph))
            # 通常の段落
            else:
                html_parts.append(f'        <p>{self._escape_html(paragraph)}</p>')
        
        return '\n'.join(html_parts)
    
    def _convert_heading(self, paragraph: str) -> str:
        """見出しをHTMLに変換"""
        level = 0
        for char in paragraph:
            if char == '#':
                level += 1
            else:
                break
        
        if level > 6:
            level = 6
        
        heading_text = paragraph[level:].strip()
        return f'        <h{level}>{self._escape_html(heading_text)}</h{level}>'
    
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