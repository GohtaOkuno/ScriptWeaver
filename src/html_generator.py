"""
HTML生成専用モジュール
処理されたコンテンツからHTML出力を生成
"""

import re
from pathlib import Path
from typing import List, Dict, Optional


class HTMLGenerator:
    """HTML生成専用クラス"""
    
    def __init__(self, css_template: str = None):
        self.css_template = css_template or self._load_default_css()
    
    def generate_html(
        self, 
        paragraphs: List[str], 
        headings: List[Dict], 
        processor,  # ContentProcessorインスタンス
        validation_report=None
    ) -> str:
        """処理されたコンテンツからHTMLを生成"""
        
        # 目次を生成
        toc_html = self._generate_toc(headings)
        
        # 段落をHTMLに変換（見出しIDを付与）
        html_body = self._process_paragraphs(paragraphs, headings, processor)
        
        # バリデーションレポートを挿入（オプション）
        validation_html = ""
        if validation_report:
            validation_html = self._generate_validation_html(validation_report)
        
        # 目次を本文の前に挿入
        if toc_html:
            html_body = f"{toc_html}\n{html_body}"
        
        # バリデーションレポートを先頭に挿入
        if validation_html:
            html_body = f"{validation_html}\n{html_body}"
        
        # 完全なHTMLドキュメントを生成
        return self._create_html_document(html_body)
    
    def _create_html_document(self, body_content: str) -> str:
        """完全なHTMLドキュメントを作成"""
        return f"""<!DOCTYPE html>
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
{body_content}
    </div>
</body>
</html>"""
    
    def _generate_toc(self, headings: List[Dict]) -> str:
        """目次HTMLを生成"""
        if not headings:
            return ""
        
        html = '        <nav class="table-of-contents">\n'
        html += '            <h2 class="toc-title">目次</h2>\n'
        html += '            <ul class="toc-list">\n'
        
        for heading in headings:
            indent = '    ' * (heading['level'] - 1)
            html += f'            {indent}<li class="toc-level-{heading["level"]}">\n'
            html += f'            {indent}    <a href="#{heading["id"]}">{self._escape_html(heading["text"])}</a>\n'
            html += f'            {indent}</li>\n'
        
        html += '            </ul>\n'
        html += '        </nav>'
        return html
    
    def _process_paragraphs(self, paragraphs: List[str], headings: List[Dict], processor) -> str:
        """段落をHTMLに変換"""
        html_parts = []
        
        # 見出しIDのマッピングを作成
        heading_ids = {heading['text']: heading['id'] for heading in headings}
        
        for paragraph in paragraphs:
            # 見出しの処理（#記号形式）
            if paragraph.startswith('#'):
                html_parts.append(self._convert_heading(paragraph, heading_ids))
            # 番号付き見出しの処理
            elif processor._is_numbered_heading(paragraph):
                html_parts.append(self._convert_numbered_heading(paragraph, heading_ids))
            # セクション区切りの処理
            elif processor.is_section_divider(paragraph):
                html_parts.append(self._convert_section_divider(paragraph, processor))
            # 表の処理
            elif processor.is_table(paragraph):
                html_parts.append(self._convert_table(paragraph, processor))
            # 定義リストの処理
            elif processor.is_definition_list(paragraph):
                html_parts.append(self._convert_definition_list(paragraph, processor))
            # 箇条書きの処理
            elif processor.is_bullet_list(paragraph):
                html_parts.append(self._convert_bullet_list(paragraph, processor))
            # NPCステータスの処理
            elif processor.is_npc_status(paragraph):
                html_parts.append(self._convert_npc_status(paragraph, processor))
            # 会話文の処理
            elif processor.has_dialogue(paragraph):
                html_parts.append(self._convert_dialogue(paragraph, processor))
            # 通常の段落
            else:
                processed_paragraph = processor.process_coc_elements(paragraph)
                html_parts.append(f'        <p>{processed_paragraph}</p>')
        
        return '\n'.join(html_parts)
    
    def _convert_heading(self, paragraph: str, heading_ids: Dict = None) -> str:
        """見出しをHTMLに変換"""
        original_level = len(paragraph) - len(paragraph.lstrip('#'))
        level = min(original_level, 6)
        heading_text = paragraph[original_level:].strip()
        
        # IDを取得
        heading_id = ""
        if heading_ids and heading_text in heading_ids:
            heading_id = f' id="{heading_ids[heading_text]}"'
        
        return f'        <h{level}{heading_id}>{self._escape_html(heading_text)}</h{level}>'
    
    def _convert_numbered_heading(self, paragraph: str, heading_ids: Dict = None) -> str:
        """番号付き見出しをHTMLに変換"""
        # 見出しレベルの判定（簡略化）
        if re.match(r'^\d+\.', paragraph):
            level = 1
        elif re.match(r'^\d+-\d+\.', paragraph):
            level = 2
        elif re.match(r'^\d+-\d+-\d+\.', paragraph):
            level = 3
        else:
            level = 2
        
        # IDを取得
        heading_id = ""
        if heading_ids and paragraph.strip() in heading_ids:
            heading_id = f' id="{heading_ids[paragraph.strip()]}"'
        
        return f'        <h{level}{heading_id}>{self._escape_html(paragraph)}</h{level}>'
    
    def _convert_section_divider(self, paragraph: str, processor) -> str:
        """セクション区切りをHTMLに変換"""
        lines = paragraph.strip().split('\n')
        html_parts = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('===') or line.startswith('---'):
                html_parts.append('        <hr class="section-divider">')
            elif line:
                processed_line = processor.process_coc_elements(line)
                html_parts.append(f'        <p>{processed_line}</p>')
        
        return '\n'.join(html_parts)
    
    def _convert_table(self, paragraph: str, processor) -> str:
        """表形式の段落をHTMLテーブルに変換"""
        lines = paragraph.strip().split('\n')
        
        # ヘッダーとボディを分離
        header_lines = []
        body_lines = []
        separator_found = False
        
        for line in lines:
            if '---' in line:
                separator_found = True
                continue
            if '|' in line:
                if not separator_found and len(header_lines) == 0:
                    header_lines.append(line)
                else:
                    body_lines.append(line)
        
        # テーブルHTML生成
        html = '        <table class="scenario-table">\n'
        
        # ヘッダー処理
        if header_lines:
            html += '            <thead>\n'
            html += '                <tr>\n'
            cells = [cell.strip() for cell in header_lines[0].split('|') if cell.strip()]
            for cell in cells:
                processed_cell = processor.process_coc_elements(cell)
                html += f'                    <th>{processed_cell}</th>\n'
            html += '                </tr>\n'
            html += '            </thead>\n'
        
        # ボディ処理
        if body_lines:
            html += '            <tbody>\n'
            for line in body_lines:
                html += '                <tr>\n'
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                for cell in cells:
                    processed_cell = processor.process_coc_elements(cell)
                    html += f'                    <td>{processed_cell}</td>\n'
                html += '                </tr>\n'
            html += '            </tbody>\n'
        
        html += '        </table>'
        return html
    
    def _convert_definition_list(self, paragraph: str, processor) -> str:
        """定義リストをHTMLに変換"""
        lines = paragraph.strip().split('\n')
        html = '        <dl class="scenario-definitions">\n'
        
        for line in lines:
            line = line.strip()
            if line.startswith('◆'):
                content = line[1:].strip()
                if '：' in content:
                    term, description = content.split('：', 1)
                elif ':' in content:
                    term, description = content.split(':', 1)
                else:
                    term = content
                    description = ''
                
                term = term.strip()
                description = description.strip()
                
                processed_term = processor.process_coc_elements(term)
                processed_desc = processor.process_coc_elements(description) if description else ''
                
                html += f'            <dt>{processed_term}</dt>\n'
                if processed_desc:
                    html += f'            <dd>{processed_desc}</dd>\n'
            elif line:
                processed_line = processor.process_coc_elements(line)
                html += f'            <p>{processed_line}</p>\n'
        
        html += '        </dl>'
        return html
    
    def _convert_bullet_list(self, paragraph: str, processor) -> str:
        """箇条書きをHTMLに変換"""
        lines = paragraph.strip().split('\n')
        html = '        <ul class="scenario-bullets">\n'
        
        for line in lines:
            line = line.strip()
            if line.startswith('・'):
                content = line[1:].strip()
                processed_content = processor.process_coc_elements(content)
                html += f'            <li>{processed_content}</li>\n'
            elif line:
                processed_line = processor.process_coc_elements(line)
                html += f'            <p>{processed_line}</p>\n'
        
        html += '        </ul>'
        return html
    
    def _convert_npc_status(self, paragraph: str, processor) -> str:
        """NPCステータスをHTMLに変換"""
        lines = paragraph.strip().split('\n')
        html = '        <div class="npc-status-block">\n'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # ステータス値を含む行
            if re.search(r'\(.*(?:STR|CON|SIZ|INT|POW|DEX|HP).*\)', line):
                match = re.match(r'^([^()]+?)\s*(\\(.*\\))(.*)$', line)
                if match:
                    npc_name = match.group(1).strip()
                    stats = match.group(2).strip()
                    other_info = match.group(3).strip()
                    
                    html += f'            <div class="npc-name">{processor.process_coc_elements(npc_name)}</div>\n'
                    if other_info:
                        html += f'            <div class="npc-note">{processor.process_coc_elements(other_info)}</div>\n'
                    html += f'            <div class="npc-stats">{processor.process_coc_elements(stats)}</div>\n'
            
            # 技能行
            elif line.startswith('技能:') or '技能:' in line:
                skills_content = re.sub(r'^.*?技能:\s*', '', line)
                html += f'            <div class="npc-skills"><strong>技能:</strong> {processor.process_coc_elements(skills_content)}</div>\n'
            
            # 装備行
            elif line.startswith('装備:') or '装備:' in line:
                equipment_content = re.sub(r'^.*?装備:\s*', '', line)
                html += f'            <div class="npc-equipment"><strong>装備:</strong> {processor.process_coc_elements(equipment_content)}</div>\n'
            
            # 攻撃手段
            elif re.search(r'(噛みつき|爪|ダメージ|\d+d\d+)', line):
                html += f'            <div class="npc-attacks"><strong>攻撃:</strong> {processor.process_coc_elements(line)}</div>\n'
            
            # その他の情報
            else:
                if line.strip():
                    html += f'            <div class="npc-other">{processor.process_coc_elements(line)}</div>\n'
        
        html += '        </div>'
        return html
    
    def _convert_dialogue(self, paragraph: str, processor) -> str:
        """会話文をHTMLに変換"""
        dialogue_pattern = re.compile(r'「([^」]+)」')
        converted = dialogue_pattern.sub(
            r'<span class="dialogue">「\1」</span>',
            paragraph
        )
        return f'        <p class="dialogue-paragraph">{converted}</p>'
    
    def _generate_validation_html(self, validation_report) -> str:
        """バリデーションレポートのHTML生成"""
        if not validation_report or len(validation_report.results) == 0:
            return ""
        
        html = '        <div class="validation-report">\n'
        html += '            <h2 class="validation-title">📋 記法チェック結果</h2>\n'
        
        # サマリー表示
        summary = validation_report.summary
        if summary["critical"] > 0:
            html += f'            <div class="validation-summary critical">🚨 重大エラー: {summary["critical"]}個</div>\n'
        if summary["warning"] > 0:
            html += f'            <div class="validation-summary warning">⚠️ 警告: {summary["warning"]}個</div>\n'
        if summary["info"] > 0:
            html += f'            <div class="validation-summary info">ℹ️ 情報: {summary["info"]}個</div>\n'
        if summary["suggestion"] > 0:
            html += f'            <div class="validation-summary suggestion">💡 提案: {summary["suggestion"]}個</div>\n'
        
        # 詳細結果
        if validation_report.results:
            html += '            <div class="validation-details">\n'
            for result in validation_report.results:
                level_class = result.level.value
                line_info = f"{result.line_number}行目: " if result.line_number else ""
                
                html += f'                <div class="validation-item {level_class}">\n'
                html += f'                    <div class="validation-message">{line_info}{self._escape_html(result.message)}</div>\n'
                
                if result.suggestion:
                    html += f'                    <div class="validation-suggestion">💡 {self._escape_html(result.suggestion)}</div>\n'
                
                if result.proposed_fix:
                    html += f'                    <div class="validation-fix">✏️ 修正案: {self._escape_html(result.proposed_fix)}</div>\n'
                
                html += '                </div>\n'
            html += '            </div>\n'
        
        html += '        </div>'
        return html
    
    def _escape_html(self, text: str) -> str:
        """HTMLエスケープ処理"""
        import html
        return html.escape(text, quote=True)
    
    def _load_default_css(self) -> str:
        """デフォルトCSSを読み込み"""
        css_path = Path(__file__).parent.parent / 'templates' / 'style.css'
        
        if css_path.exists():
            try:
                with open(css_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                pass
        
        # フォールバック用の基本CSS
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
        """