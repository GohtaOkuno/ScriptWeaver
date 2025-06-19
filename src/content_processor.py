"""
コンテンツ処理専用モジュール
TRPGシナリオテキストの解析・構造化・TRPG記法処理を担当
"""

import re
from typing import List, Dict
from functools import lru_cache


class ContentProcessor:
    """コンテンツ処理専用クラス"""
    
    def __init__(self):
        # 正規表現パターンを事前コンパイル（パフォーマンス改善）
        self._compile_patterns()
    
    def _compile_patterns(self):
        """正規表現パターンを事前コンパイル"""
        # CoC6版記法パターン
        self.skill_pattern = re.compile(r'【([^】]+)】')
        self.item_pattern = re.compile(r'『([^』]+)』')
        self.dice_pattern = re.compile(r'(\d+[dD]\d+(?:[+\-]\d+)?)', re.IGNORECASE)
        self.san_pattern = re.compile(r'(SANc?\d+/\d+(?:d\d+)?(?:[+\-]\d+)?)')
        self.dialogue_pattern = re.compile(r'「([^」]+)」')
        
        # 見出しパターン
        self.numbered_heading_patterns = [
            re.compile(r'^(\d+)\.\s+(.+)'),           # 1. タイトル
            re.compile(r'^(\d+)\.(.+)'),              # 1.タイトル
            re.compile(r'^(\d+-\d+)\.\s+(.+)'),       # 1-1. サブタイトル
            re.compile(r'^(\d+-\d+)\.(.+)'),          # 1-1.サブタイトル
            re.compile(r'^(\d+-\d+-\d+)\.\s+(.+)'),   # 1-1-1. 詳細タイトル
            re.compile(r'^(\d+-\d+-\d+)\.(.+)'),      # 1-1-1.詳細タイトル
        ]
        
        # 構造要素パターン
        self.section_divider_pattern = re.compile(r'^(===+|---+)')
        self.definition_marker_pattern = re.compile(r'^◆\s*(.+)')
        self.bullet_marker_pattern = re.compile(r'^・\s*(.+)')
        self.npc_status_pattern = re.compile(r'\(.*(?:STR|CON|SIZ|INT|POW|DEX|HP).*\)')
    
    def split_paragraphs(self, content: str) -> List[str]:
        """テキストを段落に分割（構造を考慮した分割）"""
        paragraphs = []
        
        # 一旦通常の段落分割
        raw_paragraphs = content.split('\n\n')
        
        for paragraph in raw_paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # セクション区切りと見出し、内容が混在している場合は分離
            separated = self._separate_structural_elements(paragraph)
            paragraphs.extend(separated)
        
        return [p for p in paragraphs if p.strip()]
    
    def _separate_structural_elements(self, paragraph: str) -> List[str]:
        """構造要素（見出し、区切り線等）を分離"""
        lines = paragraph.split('\n')
        result = []
        current_group = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # セクション区切り線の場合
            if self.section_divider_pattern.match(line):
                # 現在のグループを保存
                if current_group:
                    result.append('\n'.join(current_group))
                    current_group = []
                # 区切り線を単独で保存
                result.append(line)
                
            # 番号付き見出しの場合
            elif self._is_numbered_heading(line):
                # 現在のグループを保存
                if current_group:
                    result.append('\n'.join(current_group))
                    current_group = []
                # 見出しを単独で保存
                result.append(line)
                
            else:
                current_group.append(line)
        
        # 残りのグループを保存
        if current_group:
            result.append('\n'.join(current_group))
        
        return result
    
    def collect_headings(self, paragraphs: List[str]) -> List[Dict]:
        """見出しを収集してIDを付与"""
        headings = []
        
        for paragraph in paragraphs:
            # #記号見出し
            if paragraph.startswith('#'):
                level = len(paragraph) - len(paragraph.lstrip('#'))
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
    
    def _is_numbered_heading(self, text: str) -> bool:
        """番号付き見出しかどうかを判定"""
        return any(pattern.match(text) for pattern in self.numbered_heading_patterns)
    
    def _determine_heading_level(self, text: str) -> int:
        """番号付き見出しのレベルを判定"""
        for i, pattern in enumerate(self.numbered_heading_patterns, 1):
            if pattern.match(text):
                # パターンのインデックスに基づいてレベルを決定
                if i <= 2:  # 1. or 1.xxx
                    return 1
                elif i <= 4:  # 1-1. or 1-1.xxx
                    return 2
                else:  # 1-1-1. or 1-1-1.xxx
                    return 3
        return 2  # デフォルト
    
    @lru_cache(maxsize=256)
    def _generate_heading_id(self, text: str) -> str:
        """見出しテキストからIDを生成（キャッシュ付き）"""
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
    
    def process_coc_elements(self, text: str) -> str:
        """CoC6版特有要素を処理"""
        # まずHTMLエスケープを実行
        escaped_text = self._escape_html(text)
        
        # エスケープ後のテキストに対してCoC6版変換を適用
        # 優先順位：SAN記法 > ダイス表記 > 技能 > アイテム
        escaped_text = self._convert_san_notation(escaped_text)
        escaped_text = self._convert_dice_notation(escaped_text)
        escaped_text = self._convert_skill_notation(escaped_text)
        escaped_text = self._convert_item_notation(escaped_text)
        
        return escaped_text
    
    def _convert_skill_notation(self, text: str) -> str:
        """【技能名】記法をHTMLに変換"""
        return self.skill_pattern.sub(r'<span class="coc-skill">【\1】</span>', text)
    
    def _convert_item_notation(self, text: str) -> str:
        """『アイテム名』記法をHTMLに変換"""
        return self.item_pattern.sub(r'<span class="coc-item">『\1』</span>', text)
    
    def _convert_dice_notation(self, text: str) -> str:
        """ダイス表記をHTMLに変換"""
        return self.dice_pattern.sub(r'<span class="coc-dice">\1</span>', text)
    
    def _convert_san_notation(self, text: str) -> str:
        """SAN減少記法をHTMLに変換"""
        return self.san_pattern.sub(r'<span class="coc-san">\1</span>', text)
    
    def _escape_html(self, text: str) -> str:
        """HTMLエスケープ処理（標準ライブラリを使用）"""
        import html
        return html.escape(text, quote=True)
    
    def is_table(self, paragraph: str) -> bool:
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
    
    def is_section_divider(self, paragraph: str) -> bool:
        """セクション区切りかどうかを判定"""
        lines = paragraph.strip().split('\n')
        return any(self.section_divider_pattern.match(line.strip()) for line in lines)
    
    def is_definition_list(self, paragraph: str) -> bool:
        """定義リスト（◆項目）かどうかを判定"""
        lines = paragraph.strip().split('\n')
        definition_lines = [line for line in lines if line.strip().startswith('◆')]
        return len(definition_lines) >= 2
    
    def is_bullet_list(self, paragraph: str) -> bool:
        """箇条書き（・項目）かどうかを判定"""
        lines = paragraph.strip().split('\n')
        bullet_lines = [line for line in lines if line.strip().startswith('・')]
        return len(bullet_lines) >= 2
    
    def is_npc_status(self, paragraph: str) -> bool:
        """NPCステータスかどうかを判定"""
        lines = paragraph.strip().split('\n')
        return any(self.npc_status_pattern.search(line) for line in lines)
    
    def has_dialogue(self, text: str) -> bool:
        """会話文（「」）が含まれているかチェック"""
        return '「' in text and '」' in text