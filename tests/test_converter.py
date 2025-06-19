"""
converter.pyのテストコード
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
try:
    from docx import Document
    from docx.text.paragraph import Paragraph
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

from src.converter import ScriptConverter


class TestScriptConverter:
    """ScriptConverterクラスのテスト"""
    
    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.converter = ScriptConverter()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """各テストメソッド実行後のクリーンアップ"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """初期化テスト"""
        converter = ScriptConverter()
        assert converter.css_template is not None
        assert isinstance(converter.css_template, str)
    
    def test_convert_txt_file(self):
        """txtファイル変換テスト"""
        # テスト用txtファイル作成
        txt_file = self.temp_dir / "test.txt"
        txt_content = "# テストタイトル\n\nこれはテスト段落です。\n\n「こんにちは」と彼は言った。"
        txt_file.write_text(txt_content, encoding='utf-8')
        
        # 変換実行
        output_file = self.converter.convert(txt_file)
        
        # 結果確認
        assert output_file.exists()
        assert output_file.suffix == '.html'
        html_content = output_file.read_text(encoding='utf-8')
        assert '<!DOCTYPE html>' in html_content
        assert '<h1>テストタイトル</h1>' in html_content
        assert '<p>これはテスト段落です。</p>' in html_content
        assert 'dialogue' in html_content
    
    @patch('src.converter.Document')
    def test_convert_docx_file(self, mock_document):
        """docxファイル変換テスト"""
        # Documentのモック設定
        mock_doc = MagicMock()
        mock_paragraph1 = MagicMock()
        mock_paragraph1.text = "# テストタイトル"
        mock_paragraph2 = MagicMock()
        mock_paragraph2.text = "これはテスト段落です。"
        mock_paragraph3 = MagicMock()
        mock_paragraph3.text = ""  # 空の段落
        mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2, mock_paragraph3]
        mock_document.return_value = mock_doc
        
        # テスト用docxファイル作成
        docx_file = self.temp_dir / "test.docx"
        docx_file.touch()  # ファイル作成
        
        # 変換実行
        output_file = self.converter.convert(docx_file)
        
        # 結果確認
        assert output_file.exists()
        assert output_file.suffix == '.html'
        html_content = output_file.read_text(encoding='utf-8')
        assert '<!DOCTYPE html>' in html_content
        assert '<h1>テストタイトル</h1>' in html_content
    
    def test_convert_unsupported_format(self):
        """対応していない形式のテスト"""
        unsupported_file = self.temp_dir / "test.pdf"
        unsupported_file.touch()
        
        with pytest.raises(ValueError, match="対応していない形式"):
            self.converter.convert(unsupported_file)
    
    def test_read_text_file(self):
        """テキストファイル読み込みテスト"""
        txt_file = self.temp_dir / "test.txt"
        content = "テストコンテンツ\n改行あり"
        txt_file.write_text(content, encoding='utf-8')
        
        result = self.converter._read_text_file(txt_file)
        assert result == content
    
    @patch('src.converter.Document')
    def test_read_docx_file(self, mock_document):
        """docxファイル読み込みテスト"""
        mock_doc = MagicMock()
        mock_paragraph1 = MagicMock()
        mock_paragraph1.text = "段落1"
        mock_paragraph2 = MagicMock()
        mock_paragraph2.text = "段落2"
        mock_paragraph3 = MagicMock()
        mock_paragraph3.text = ""  # 空の段落
        mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2, mock_paragraph3]
        mock_document.return_value = mock_doc
        
        docx_file = self.temp_dir / "test.docx"
        result = self.converter._read_docx_file(docx_file)
        
        assert result == "段落1\n\n段落2"
    
    def test_convert_to_html(self):
        """HTML変換テスト"""
        content = "# タイトル\n\n段落テスト\n\n「会話テスト」"
        result = self.converter._convert_to_html(content)
        
        assert '<!DOCTYPE html>' in result
        assert '<html lang="ja">' in result
        assert '<meta charset="UTF-8">' in result
        assert '<h1>タイトル</h1>' in result
        assert '<p>段落テスト</p>' in result
        assert 'dialogue' in result
    
    def test_split_paragraphs(self):
        """段落分割テスト"""
        content = "段落1\n\n段落2\n\n\n段落3\n\n"
        result = self.converter._split_paragraphs(content)
        
        assert result == ["段落1", "段落2", "段落3"]
    
    def test_process_paragraphs(self):
        """段落処理テスト"""
        paragraphs = [
            "# 見出し1",
            "## 見出し2",
            "通常の段落",
            "「会話文」を含む段落"
        ]
        result = self.converter._process_paragraphs(paragraphs)
        
        assert '<h1>見出し1</h1>' in result
        assert '<h2>見出し2</h2>' in result
        assert '<p>通常の段落</p>' in result
        assert 'dialogue' in result
    
    def test_convert_heading(self):
        """見出し変換テスト"""
        # h1テスト
        result = self.converter._convert_heading("# 見出し1")
        assert result == '        <h1>見出し1</h1>'
        
        # h2テスト
        result = self.converter._convert_heading("## 見出し2")
        assert result == '        <h2>見出し2</h2>'
        
        # h6を超える場合
        result = self.converter._convert_heading("####### 見出し7")
        assert result == '        <h6>見出し7</h6>'
    
    def test_convert_dialogue(self):
        """会話文変換テスト"""
        paragraph = "彼は「こんにちは」と言った。"
        result = self.converter._convert_dialogue(paragraph)
        
        assert 'dialogue-paragraph' in result
        assert '<span class="dialogue">「こんにちは」</span>' in result
    
    def test_escape_html(self):
        """HTMLエスケープテスト"""
        text = "<script>alert('test');</script> & \"quote\" 'single'"
        result = self.converter._escape_html(text)
        
        assert '&lt;script&gt;' in result
        assert '&amp;' in result
        assert '&quot;' in result
        assert '&#x27;' in result
    
    @patch('builtins.open', mock_open(read_data="test css content"))
    @patch('pathlib.Path.exists')
    def test_load_css_template_with_file(self, mock_exists):
        """CSSテンプレート読み込みテスト（ファイルあり）"""
        mock_exists.return_value = True
        
        converter = ScriptConverter()
        assert converter.css_template == "test css content"
    
    @patch('pathlib.Path.exists')
    def test_load_css_template_without_file(self, mock_exists):
        """CSSテンプレート読み込みテスト（ファイルなし）"""
        mock_exists.return_value = False
        
        converter = ScriptConverter()
        assert 'body {' in converter.css_template
        assert 'font-family:' in converter.css_template
    
    def test_sample_scenario_conversion(self):
        """サンプルシナリオ変換テスト"""
        # サンプルファイルのパス
        sample_file = Path("samples/input/sample_scenario.txt")
        expected_file = Path("samples/expected_output/sample_scenario.html")
        
        # サンプルファイルが存在することを確認
        if not sample_file.exists():
            pytest.skip("サンプルファイルが存在しません")
        
        # 変換実行
        output_file = self.converter.convert(sample_file)
        
        # 基本的な構造の確認
        html_content = output_file.read_text(encoding='utf-8')
        assert '<!DOCTYPE html>' in html_content
        assert '<html lang="ja">' in html_content
        assert '<h1>森の中の古い館</h1>' in html_content
        assert '<h2>プロローグ</h2>' in html_content
        assert '<h2>第1章：館の内部</h2>' in html_content
        assert '<h3>食堂の調査</h3>' in html_content
        assert 'dialogue' in html_content  # 会話文のクラスが含まれていることを確認
        
        # クリーンアップ
        if output_file.exists():
            output_file.unlink()
    
    def test_sample_dialogue_detection(self):
        """サンプルシナリオの会話文検出テスト"""
        content = """
# テストシナリオ

「何だ、この古い建物は...」
冒険者の一人が呟く。

「まるで、住人が突然いなくなったようだ」

「この彫像...何かがおかしい」
        """.strip()
        
        html_result = self.converter._convert_to_html(content)
        
        # 会話文が適切に検出・変換されていることを確認
        assert 'dialogue-paragraph' in html_result
        assert '「何だ、この古い建物は...」' in html_result
        assert '「まるで、住人が突然いなくなったようだ」' in html_result
        assert '「この彫像...何かがおかしい」' in html_result
    
    def test_is_numbered_heading(self):
        """番号付き見出し判定テスト"""
        # 番号付き見出しのテスト（スペースあり）
        assert self.converter._is_numbered_heading("1. 概要") == True
        assert self.converter._is_numbered_heading("2-1. サブセクション") == True
        assert self.converter._is_numbered_heading("3-2-1. 詳細項目") == True
        
        # 番号付き見出しのテスト（スペースなし）
        assert self.converter._is_numbered_heading("1.概要") == True
        assert self.converter._is_numbered_heading("2-1.サブセクション") == True
        assert self.converter._is_numbered_heading("3-2-1.詳細項目") == True
        
        # 番号付き見出しではないもの
        assert self.converter._is_numbered_heading("# 通常の見出し") == False
        assert self.converter._is_numbered_heading("普通の段落") == False
        assert self.converter._is_numbered_heading("1 ピリオドなし") == False
        assert self.converter._is_numbered_heading("a. アルファベットはダメ") == False
    
    def test_determine_heading_level(self):
        """見出しレベル判定テスト"""
        assert self.converter._determine_heading_level("1. メインタイトル") == 1
        assert self.converter._determine_heading_level("2. 別のメインタイトル") == 1
        assert self.converter._determine_heading_level("1-1. サブタイトル") == 2
        assert self.converter._determine_heading_level("2-3. 別のサブタイトル") == 2
        assert self.converter._determine_heading_level("1-2-1. 詳細タイトル") == 3
        assert self.converter._determine_heading_level("3-1-5. 別の詳細") == 3
    
    def test_extract_heading_text(self):
        """見出しテキスト抽出テスト"""
        assert self.converter._extract_heading_text("1. 概要") == "概要"
        assert self.converter._extract_heading_text("2-1. 背景情報") == "背景情報"
        assert self.converter._extract_heading_text("3-2-1. 詳細な説明") == "詳細な説明"
        assert self.converter._extract_heading_text("10-5-2. 複数桁も対応") == "複数桁も対応"
    
    def test_convert_numbered_heading(self):
        """番号付き見出し変換テスト"""
        # h1変換テスト
        result = self.converter._convert_numbered_heading("1. 概要")
        assert '<h1>1. 概要</h1>' in result
        
        # h2変換テスト
        result = self.converter._convert_numbered_heading("2-1. 背景")
        assert '<h2>2-1. 背景</h2>' in result
        
        # h3変換テスト
        result = self.converter._convert_numbered_heading("3-1-2. 詳細")
        assert '<h3>3-1-2. 詳細</h3>' in result
    
    def test_numbered_heading_integration(self):
        """番号付き見出し統合テスト"""
        content = """1. TRPGシナリオ概要

このシナリオは森の館を舞台とします。

2. 背景設定

昔、この館には...

2-1. 主要NPCについて

館の主人は既に亡くなっており...

2-1-1. 館の主人の詳細

名前: エドワード・ブラックウッド

3. ゲーム進行

以下の手順で進めてください。"""
        
        html_result = self.converter._convert_to_html(content)
        
        # 各レベルの見出しが適切に変換されていることを確認
        assert '<h1>1. TRPGシナリオ概要</h1>' in html_result
        assert '<h1>2. 背景設定</h1>' in html_result
        assert '<h2>2-1. 主要NPCについて</h2>' in html_result
        assert '<h3>2-1-1. 館の主人の詳細</h3>' in html_result
        assert '<h1>3. ゲーム進行</h1>' in html_result
        
        # 通常の段落も適切に変換されていることを確認
        assert '<p>このシナリオは森の館を舞台とします。</p>' in html_result
        assert '<p>昔、この館には...</p>' in html_result
    
    def test_convert_skill_notation(self):
        """【技能名】記法変換テスト"""
        result = self.converter._convert_skill_notation("【図書館】で調べると【目星】で発見できる")
        expected = '<span class="coc-skill">【図書館】</span>で調べると<span class="coc-skill">【目星】</span>で発見できる'
        assert result == expected
        
        # 複雑な技能名のテスト
        result = self.converter._convert_skill_notation("【機械修理orコンピュータ-20】判定")
        expected = '<span class="coc-skill">【機械修理orコンピュータ-20】</span>判定'
        assert result == expected
    
    def test_convert_item_notation(self):
        """『アイテム名』記法変換テスト"""
        result = self.converter._convert_item_notation("『Class：Red』と『silver bullet』を発見")
        expected = '<span class="coc-item">『Class：Red』</span>と<span class="coc-item">『silver bullet』</span>を発見'
        assert result == expected
    
    def test_convert_dice_notation(self):
        """ダイス表記変換テスト"""
        result = self.converter._convert_dice_notation("1d4+1のダメージ、2d6判定、3d10ロール")
        expected = '<span class="coc-dice">1d4+1</span>のダメージ、<span class="coc-dice">2d6</span>判定、<span class="coc-dice">3d10</span>ロール'
        assert result == expected
        
        # マイナス修正のテスト
        result = self.converter._convert_dice_notation("1d100-20で判定")
        expected = '<span class="coc-dice">1d100-20</span>で判定'
        assert result == expected
    
    def test_convert_san_notation(self):
        """SAN減少記法変換テスト"""
        result = self.converter._convert_san_notation("【SANc1/1d4】の狂気を得る、SANc0/1の減少")
        expected = '【<span class="coc-san">SANc1/1d4</span>】の狂気を得る、<span class="coc-san">SANc0/1</span>の減少'
        assert result == expected
        
        # 複雑なSAN表記のテスト
        result = self.converter._convert_san_notation("SANc1/1d8+1")
        expected = '<span class="coc-san">SANc1/1d8+1</span>'
        assert result == expected
    
    def test_process_coc_elements_integration(self):
        """CoC6版要素統合処理テスト"""
        text = "【図書館】で『古い日記』を発見。1d4+1のダメージ、SANc1/1d6の減少"
        result = self.converter._process_coc_elements(text)
        
        # 各要素が適切に変換されていることを確認
        assert '<span class="coc-skill">【図書館】</span>' in result
        assert '<span class="coc-item">『古い日記』</span>' in result
        assert '<span class="coc-dice">1d4+1</span>' in result
        # SAN記法は優先処理されるため、内部にダイス表記が含まれる
        assert 'coc-san' in result and 'SANc1' in result
        
        # HTMLエスケープも適用されていることを確認
        assert '&lt;' not in result  # この例では特殊文字がないため
    
    def test_coc_elements_in_paragraph_conversion(self):
        """段落変換でのCoC6版要素テスト"""
        content = """1. 調査開始

【目星】判定で『重要な手がかり』を発見する。

2d6のダメージを受け、SANc0/1d4の減少。

「恐ろしい光景だ」と探索者は呟く。"""
        
        html_result = self.converter._convert_to_html(content)
        
        # 見出しの変換確認
        assert '<h1>1. 調査開始</h1>' in html_result
        
        # CoC6版要素の変換確認
        assert '<span class="coc-skill">【目星】</span>' in html_result
        assert '<span class="coc-item">『重要な手がかり』</span>' in html_result
        assert '<span class="coc-dice">2d6</span>' in html_result
        # SAN記法は優先処理されるため、内部にダイス表記が含まれる可能性
        assert 'coc-san' in html_result and 'SANc0' in html_result
        
        # 会話文の変換確認
        assert 'dialogue-paragraph' in html_result
    
    def test_is_table(self):
        """表の判定テスト"""
        # パイプ文字とセパレータがある表
        table_text = """時刻　| 出来事
------|-----------------------------------------------
14:00 | PCの乗る「宇江田バス」久禮波駅着
17:30 | 防潮壁で低い軋み音（初〈聞き耳〉）"""
        assert self.converter._is_table(table_text) == True
        
        # パイプ文字だけの表（セパレータなし）
        simple_table = """項目 | 値
データ1 | 結果1
データ2 | 結果2"""
        assert self.converter._is_table(simple_table) == True
        
        # 通常の段落
        normal_text = "これは通常の段落です。表ではありません。"
        assert self.converter._is_table(normal_text) == False
        
        # 1行だけの場合
        single_line = "項目 | 値"
        assert self.converter._is_table(single_line) == False
    
    def test_convert_table(self):
        """表の変換テスト"""
        table_text = """時刻　| 出来事
------|-----------------------------------------------
14:00 | PCの乗る「宇江田バス」久禮波駅着
17:30 | 防潮壁で低い軋み音（初〈聞き耳〉）
19:00 | 町内放送「潮鳴祭の復活」を宣言"""
        
        result = self.converter._convert_table(table_text)
        
        # テーブル要素の確認
        assert '<table class="scenario-table">' in result
        assert '<thead>' in result
        assert '<tbody>' in result
        assert '<th>時刻</th>' in result
        assert '<th>出来事</th>' in result
        assert '<td>14:00</td>' in result
        assert '<td>PCの乗る「宇江田バス」久禮波駅着</td>' in result
        
        # CoC要素も変換されることを確認
        assert '〈聞き耳〉' in result
    
    def test_convert_table_with_coc_elements(self):
        """CoC要素を含む表の変換テスト"""
        table_text = """項目　　　| 成功/取得条件 | SAN変化
------------|---------------|---------
封印成功　　| 扉破壊＋符　 | +1D6
逃走成功　　| 全員生還　　 | +1D4
深尾を保護　| 廃屋で同行　| +1"""
        
        result = self.converter._convert_table(table_text)
        
        # テーブル構造の確認
        assert '<table class="scenario-table">' in result
        assert '<th>項目</th>' in result
        assert '<th>成功/取得条件</th>' in result
        assert '<th>SAN変化</th>' in result
        
        # CoC要素の変換確認
        assert '+1D6' in result  # ダイス表記
        assert '+1D4' in result  # ダイス表記
        
    def test_table_in_paragraph_conversion(self):
        """段落変換での表認識テスト"""
        content = """# タイムライン

時刻　| 出来事
------|-----------------------------------------------
14:00 | PCの乗る「宇江田バス」久禮波駅着
17:30 | 防潮壁で低い軋み音

通常の段落です。"""
        
        html_result = self.converter._convert_to_html(content)
        
        # 見出しの変換確認
        assert '<h1>タイムライン</h1>' in html_result
        
        # 表の変換確認
        assert '<table class="scenario-table">' in html_result
        assert '<th>時刻</th>' in html_result
        assert '<th>出来事</th>' in html_result
        assert '<td>14:00</td>' in html_result
        
        # 通常段落の確認
        assert '<p>通常の段落です。</p>' in html_result