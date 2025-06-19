"""
ScriptWeaver変換処理モジュール
.txt/.docx ファイルをHTMLに変換する機能を提供
"""

import re
from pathlib import Path
from typing import List, Optional
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


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
        # エンコーディング検出
        encodings = ['utf-8', 'shift_jis', 'cp932', 'euc-jp', 'iso-2022-jp']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        # 全てのエンコーディングが失敗した場合はエラー
        raise ValueError(f"ファイルのエンコーディングを特定できませんでした: {file_path}")
    
    def _read_docx_file(self, file_path: Path) -> str:
        """Word文書を読み込み"""
        if not DOCX_AVAILABLE:
            raise ImportError("python-docxがインストールされていません。pip install python-docxを実行してください。")
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
        
        # 見出しを収集して目次を生成
        headings = self._collect_headings(paragraphs)
        toc_html = self._generate_toc(headings)
        
        # 段落をHTMLに変換（見出しIDを付与）
        html_body = self._process_paragraphs(paragraphs, headings)
        
        # 目次を本文の前に挿入
        if toc_html:
            html_body = f"{toc_html}\n{html_body}"
        
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
        """テキストを段落に分割（構造を考慮した分割）"""
        paragraphs = []
        
        # 一旦通常の段落分割
        raw_paragraphs = content.split('\n\n')
        
        for paragraph in raw_paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # セクション区切りと見出し、内容が混在している場合は分離
            lines = paragraph.split('\n')
            
            current_group = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # セクション区切り線の場合
                if line.startswith('===') or line.startswith('---'):
                    # 現在のグループを保存
                    if current_group:
                        paragraphs.append('\n'.join(current_group))
                        current_group = []
                    # 区切り線を単独で保存
                    paragraphs.append(line)
                    
                # 番号付き見出しの場合
                elif re.match(r'^\d+\.\s+.+', line) or re.match(r'^\d+\..+', line):
                    # 現在のグループを保存
                    if current_group:
                        paragraphs.append('\n'.join(current_group))
                        current_group = []
                    # 見出しを単独で保存
                    paragraphs.append(line)
                    
                else:
                    current_group.append(line)
            
            # 残りのグループを保存
            if current_group:
                paragraphs.append('\n'.join(current_group))
        
        return [p for p in paragraphs if p.strip()]
    
    def _collect_headings(self, paragraphs: List[str]) -> List[dict]:
        """見出しを収集"""
        headings = []
        
        for paragraph in paragraphs:
            # #記号見出し
            if paragraph.startswith('#'):
                level = 0
                for char in paragraph:
                    if char == '#':
                        level += 1
                    else:
                        break
                text = paragraph[level:].strip()
                headings.append({
                    'text': text,
                    'level': level,
                    'id': self._generate_heading_id(text),
                    'type': 'hash'
                })
            
            # 番号付き見出し
            elif self._is_numbered_heading(paragraph):
                level = self._determine_heading_level(paragraph)
                headings.append({
                    'text': paragraph.strip(),
                    'level': level,
                    'id': self._generate_heading_id(paragraph),
                    'type': 'numbered'
                })
        
        return headings
    
    def _generate_heading_id(self, text: str) -> str:
        """見出しテキストからIDを生成"""
        import unicodedata
        # 特殊文字を除去し、英数字とハイフンのみに
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        text = text.strip('-').lower()
        
        # 日本語の場合は数字部分のみ使用
        if re.match(r'^\d+', text):
            number_match = re.match(r'^(\d+(?:-\d+)*)', text)
            if number_match:
                return f"heading-{number_match.group(1)}"
        
        # 英数字がない場合はハッシュ値を使用
        if not text or not re.search(r'[a-zA-Z0-9]', text):
            import hashlib
            return f"heading-{hashlib.md5(text.encode()).hexdigest()[:8]}"
        
        return f"heading-{text}"
    
    def _generate_toc(self, headings: List[dict]) -> str:
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
    
    def _process_paragraphs(self, paragraphs: List[str], headings: List[dict] = None) -> str:
        """段落をHTMLに変換"""
        html_parts = []
        
        # 見出しIDのマッピングを作成
        heading_ids = {}
        if headings:
            for heading in headings:
                heading_ids[heading['text']] = heading['id']
        
        for paragraph in paragraphs:
            # 見出しの処理（#記号形式）
            if paragraph.startswith('#'):
                html_parts.append(self._convert_heading(paragraph, heading_ids))
            # 番号付き見出しの処理（1. 2-1. 等）
            elif self._is_numbered_heading(paragraph):
                html_parts.append(self._convert_numbered_heading(paragraph, heading_ids))
            # セクション区切りの処理
            elif self._is_section_divider(paragraph):
                html_parts.append(self._convert_section_divider(paragraph))
            # 表の処理（パイプ文字を含む）
            elif self._is_table(paragraph):
                html_parts.append(self._convert_table(paragraph))
            # 定義リストの処理（◆項目）
            elif self._is_definition_list(paragraph):
                html_parts.append(self._convert_definition_list(paragraph))
            # 箇条書きの処理（・項目）
            elif self._is_bullet_list(paragraph):
                html_parts.append(self._convert_bullet_list(paragraph))
            # NPCステータスの処理
            elif self._is_npc_status(paragraph):
                html_parts.append(self._convert_npc_status(paragraph))
            # 会話文の処理（「」で囲まれた文）
            elif '「' in paragraph and '」' in paragraph:
                html_parts.append(self._convert_dialogue(paragraph))
            # 通常の段落（CoC6版要素を含む可能性）
            else:
                processed_paragraph = self._process_coc_elements(paragraph)
                html_parts.append(f'        <p>{processed_paragraph}</p>')
        
        return '\n'.join(html_parts)
    
    def _convert_heading(self, paragraph: str, heading_ids: dict = None) -> str:
        """見出しをHTMLに変換"""
        original_level = 0
        for char in paragraph:
            if char == '#':
                original_level += 1
            else:
                break
        
        level = min(original_level, 6)
        heading_text = paragraph[original_level:].strip()
        
        # IDを取得
        heading_id = ""
        if heading_ids and heading_text in heading_ids:
            heading_id = f' id="{heading_ids[heading_text]}"'
        
        return f'        <h{level}{heading_id}>{self._escape_html(heading_text)}</h{level}>'
    
    def _is_numbered_heading(self, paragraph: str) -> bool:
        """番号付き見出しかどうかを判定"""
        # 番号付き見出しのパターン（スペースあり・なし両方対応）
        patterns = [
            r'^\d+\.\s+.+',           # 1. タイトル（スペース必須）
            r'^\d+\..+',              # 1.タイトル（スペースなし）
            r'^\d+-\d+\.\s+.+',       # 1-1. サブタイトル（スペース必須）
            r'^\d+-\d+\..+',          # 1-1.サブタイトル（スペースなし）
            r'^\d+-\d+-\d+\.\s+.+',   # 1-1-1. 詳細タイトル（スペース必須）
            r'^\d+-\d+-\d+\..+',      # 1-1-1.詳細タイトル（スペースなし）
        ]
        
        for pattern in patterns:
            if re.match(pattern, paragraph):
                return True
        return False
    
    def _convert_numbered_heading(self, paragraph: str, heading_ids: dict = None) -> str:
        """番号付き見出しをHTMLに変換"""
        # 見出しレベルの判定
        level = self._determine_heading_level(paragraph)
        
        # IDを取得
        heading_id = ""
        if heading_ids and paragraph.strip() in heading_ids:
            heading_id = f' id="{heading_ids[paragraph.strip()]}"'
        
        return f'        <h{level}{heading_id}>{self._escape_html(paragraph)}</h{level}>'
    
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
    
    def _is_table(self, paragraph: str) -> bool:
        """段落が表形式かどうかを判定"""
        lines = paragraph.strip().split('\n')
        if len(lines) < 2:
            return False
        
        # パイプ文字を含む行が2行以上あるかチェック
        pipe_lines = [line for line in lines if '|' in line]
        if len(pipe_lines) < 2:
            return False
        
        # セパレータ行（---）があるかチェック
        has_separator = any('-' * 3 in line for line in lines)
        
        return has_separator or len(pipe_lines) >= 2
    
    def _convert_table(self, paragraph: str) -> str:
        """表形式の段落をHTMLテーブルに変換"""
        lines = paragraph.strip().split('\n')
        table_lines = []
        
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
                processed_cell = self._process_coc_elements(cell)
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
                    processed_cell = self._process_coc_elements(cell)
                    html += f'                    <td>{processed_cell}</td>\n'
                html += '                </tr>\n'
            html += '            </tbody>\n'
        
        html += '        </table>'
        return html
    
    def _is_section_divider(self, paragraph: str) -> bool:
        """セクション区切りかどうかを判定"""
        lines = paragraph.strip().split('\n')
        # === または --- で始まる行があるかチェック
        return any(line.strip().startswith('===') or line.strip().startswith('---') for line in lines)
    
    def _convert_section_divider(self, paragraph: str) -> str:
        """セクション区切りをHTMLに変換"""
        lines = paragraph.strip().split('\n')
        html_parts = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('===') or line.startswith('---'):
                html_parts.append('        <hr class="section-divider">')
            elif line:
                # 区切り線以外のテキストは通常の段落として処理
                processed_line = self._process_coc_elements(line)
                html_parts.append(f'        <p>{processed_line}</p>')
        
        return '\n'.join(html_parts)
    
    def _is_definition_list(self, paragraph: str) -> bool:
        """定義リスト（◆項目）かどうかを判定"""
        lines = paragraph.strip().split('\n')
        # ◆で始まる行が2行以上あるかチェック
        definition_lines = [line for line in lines if line.strip().startswith('◆')]
        return len(definition_lines) >= 2
    
    def _convert_definition_list(self, paragraph: str) -> str:
        """定義リストをHTMLに変換"""
        lines = paragraph.strip().split('\n')
        html = '        <dl class="scenario-definitions">\n'
        
        for line in lines:
            line = line.strip()
            if line.startswith('◆'):
                # ◆項目名　: 内容 の形式を処理
                content = line[1:].strip()  # ◆を除去
                if '：' in content:
                    term, description = content.split('：', 1)
                    term = term.strip()
                    description = description.strip()
                elif ':' in content:
                    term, description = content.split(':', 1)
                    term = term.strip()
                    description = description.strip()
                else:
                    term = content
                    description = ''
                
                processed_term = self._process_coc_elements(term)
                processed_desc = self._process_coc_elements(description) if description else ''
                
                html += f'            <dt>{processed_term}</dt>\n'
                if processed_desc:
                    html += f'            <dd>{processed_desc}</dd>\n'
            elif line:
                # ◆以外の行は通常の段落として処理
                processed_line = self._process_coc_elements(line)
                html += f'            <p>{processed_line}</p>\n'
        
        html += '        </dl>'
        return html
    
    def _is_bullet_list(self, paragraph: str) -> bool:
        """箇条書き（・項目）かどうかを判定"""
        lines = paragraph.strip().split('\n')
        # ・で始まる行が2行以上あるかチェック
        bullet_lines = [line for line in lines if line.strip().startswith('・')]
        return len(bullet_lines) >= 2
    
    def _convert_bullet_list(self, paragraph: str) -> str:
        """箇条書きをHTMLに変換"""
        lines = paragraph.strip().split('\n')
        html = '        <ul class="scenario-bullets">\n'
        
        for line in lines:
            line = line.strip()
            if line.startswith('・'):
                content = line[1:].strip()  # ・を除去
                processed_content = self._process_coc_elements(content)
                html += f'            <li>{processed_content}</li>\n'
            elif line:
                # ・以外の行は通常の段落として処理
                processed_line = self._process_coc_elements(line)
                html += f'            <p>{processed_line}</p>\n'
        
        html += '        </ul>'
        return html
    
    def _is_npc_status(self, paragraph: str) -> bool:
        """NPCステータスかどうかを判定"""
        lines = paragraph.strip().split('\n')
        # ステータス値を含む行があるかチェック（STR、CON、HPなどを含む）
        status_pattern = r'\(.*(?:STR|CON|SIZ|INT|POW|DEX|HP).*\)'
        return any(re.search(status_pattern, line) for line in lines)
    
    def _convert_npc_status(self, paragraph: str) -> str:
        """NPCステータスをHTMLに変換"""
        lines = paragraph.strip().split('\n')
        html = '        <div class="npc-status-block">\n'
        
        npc_name = ""
        stats = ""
        skills = ""
        equipment = ""
        other_info = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # ステータス値を含む行（キャラクター名と基本能力値）
            if re.search(r'\(.*(?:STR|CON|SIZ|INT|POW|DEX|HP).*\)', line):
                # 名前部分とステータス部分を分離
                match = re.match(r'^([^()]+?)[\s　]*(\(.*\))(.*)$', line)
                if match:
                    npc_name = match.group(1).strip()
                    stats = match.group(2).strip()
                    other_info = match.group(3).strip()
                    
                    html += f'            <div class="npc-name">{self._process_coc_elements(npc_name)}</div>\n'
                    if other_info:
                        html += f'            <div class="npc-note">{self._process_coc_elements(other_info)}</div>\n'
                    html += f'            <div class="npc-stats">{self._process_coc_elements(stats)}</div>\n'
                
            # 技能行
            elif line.startswith('技能:') or '技能:' in line:
                skills_content = re.sub(r'^.*?技能:\s*', '', line)
                html += f'            <div class="npc-skills"><strong>技能:</strong> {self._process_coc_elements(skills_content)}</div>\n'
                
            # 装備行
            elif line.startswith('装備:') or '装備:' in line:
                equipment_content = re.sub(r'^.*?装備:\s*', '', line)
                html += f'            <div class="npc-equipment"><strong>装備:</strong> {self._process_coc_elements(equipment_content)}</div>\n'
                
            # 攻撃手段（噛みつき、爪など）
            elif re.search(r'(噛みつき|爪|ダメージ|\d+d\d+)', line):
                html += f'            <div class="npc-attacks"><strong>攻撃:</strong> {self._process_coc_elements(line)}</div>\n'
                
            # その他の情報
            else:
                if line.strip():
                    html += f'            <div class="npc-other">{self._process_coc_elements(line)}</div>\n'
        
        html += '        </div>'
        return html
    
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