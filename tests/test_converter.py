"""
converter.pyのテストコード
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from docx import Document
from docx.text.paragraph import Paragraph

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