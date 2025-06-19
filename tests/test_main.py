"""
main.pyのテストコード
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

# main.pyのインポート
import main


class TestMain:
    """main.pyのテスト"""
    
    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_argv = sys.argv.copy()
    
    def teardown_method(self):
        """各テストメソッド実行後のクリーンアップ"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        sys.argv = self.original_argv
    
    def test_main_no_arguments(self, capsys):
        """引数なしでのmain関数テスト"""
        sys.argv = ['main.py']
        
        with pytest.raises(SystemExit) as exc_info:
            main.main()
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "使用方法: python main.py <input_file>" in captured.out
        assert "対応形式: .txt, .docx" in captured.out
    
    def test_main_too_many_arguments(self, capsys):
        """引数が多すぎる場合のテスト"""
        sys.argv = ['main.py', 'file1.txt', 'file2.txt']
        
        with pytest.raises(SystemExit) as exc_info:
            main.main()
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "使用方法: python main.py <input_file>" in captured.out
    
    def test_main_file_not_found(self, capsys):
        """存在しないファイルを指定した場合のテスト"""
        non_existent_file = self.temp_dir / "non_existent.txt"
        sys.argv = ['main.py', str(non_existent_file)]
        
        with pytest.raises(SystemExit) as exc_info:
            main.main()
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert f"エラー: ファイルが見つかりません: {non_existent_file}" in captured.out
    
    def test_main_unsupported_format(self, capsys):
        """対応していない形式のファイルを指定した場合のテスト"""
        unsupported_file = self.temp_dir / "test.pdf"
        unsupported_file.touch()
        sys.argv = ['main.py', str(unsupported_file)]
        
        with pytest.raises(SystemExit) as exc_info:
            main.main()
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "エラー: 対応していない形式です: .pdf" in captured.out
        assert "対応形式: .txt, .docx" in captured.out
    
    @patch('main.ScriptConverter')
    def test_main_successful_conversion(self, mock_converter_class, capsys):
        """正常な変換処理のテスト"""
        # テスト用txtファイル作成
        txt_file = self.temp_dir / "test.txt"
        txt_file.write_text("テストコンテンツ", encoding='utf-8')
        output_file = self.temp_dir / "test.html"
        
        # ScriptConverterのモック設定
        mock_converter = MagicMock()
        mock_converter.convert.return_value = output_file
        mock_converter_class.return_value = mock_converter
        
        sys.argv = ['main.py', str(txt_file)]
        
        main.main()
        
        # モックが正しく呼ばれたか確認
        mock_converter_class.assert_called_once()
        mock_converter.convert.assert_called_once_with(txt_file)
        
        # 出力メッセージ確認
        captured = capsys.readouterr()
        assert f"読み込み開始: {txt_file}" in captured.out
        assert f"変換完了: {output_file}" in captured.out
    
    @patch('main.ScriptConverter')
    def test_main_conversion_exception(self, mock_converter_class, capsys):
        """変換処理で例外が発生した場合のテスト"""
        # テスト用txtファイル作成
        txt_file = self.temp_dir / "test.txt"
        txt_file.write_text("テストコンテンツ", encoding='utf-8')
        
        # ScriptConverterのモック設定（例外を発生）
        mock_converter = MagicMock()
        mock_converter.convert.side_effect = Exception("変換エラー")
        mock_converter_class.return_value = mock_converter
        
        sys.argv = ['main.py', str(txt_file)]
        
        with pytest.raises(SystemExit) as exc_info:
            main.main()
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "変換失敗: 変換エラー" in captured.out
    
    def test_main_txt_file_format(self, capsys):
        """txtファイル形式の処理テスト"""
        txt_file = self.temp_dir / "test.txt"
        txt_file.write_text("テストコンテンツ", encoding='utf-8')
        
        with patch('main.ScriptConverter') as mock_converter_class:
            mock_converter = MagicMock()
            output_file = self.temp_dir / "test.html"
            mock_converter.convert.return_value = output_file
            mock_converter_class.return_value = mock_converter
            
            sys.argv = ['main.py', str(txt_file)]
            main.main()
            
            # 正しいファイルパスが渡されたか確認
            mock_converter.convert.assert_called_once_with(txt_file)
    
    @patch('main.main')
    def test_main_module_execution(self, mock_main):
        """モジュール実行時のテスト"""
        # mainモジュールを直接インポートして__name__を設定
        import main as main_module
        
        # __name__を__main__に設定してモジュールレベルの実行をシミュレート
        original_name = main_module.__name__
        try:
            main_module.__name__ = '__main__'
            # モジュールの最後の部分を実行
            exec("if __name__ == '__main__': main()", main_module.__dict__)
            mock_main.assert_called_once()
        finally:
            main_module.__name__ = original_name
    
    def test_main_docx_file_format(self, capsys):
        """docxファイル形式の処理テスト"""
        docx_file = self.temp_dir / "test.docx"
        docx_file.touch()
        
        with patch('main.ScriptConverter') as mock_converter_class:
            mock_converter = MagicMock()
            output_file = self.temp_dir / "test.html"
            mock_converter.convert.return_value = output_file
            mock_converter_class.return_value = mock_converter
            
            sys.argv = ['main.py', str(docx_file)]
            main.main()
            
            # 正しいファイルパスが渡されたか確認
            mock_converter.convert.assert_called_once_with(docx_file)
    
    def test_main_case_insensitive_extension(self, capsys):
        """拡張子の大文字小文字を区別しないテスト"""
        # 大文字の拡張子でテスト
        txt_file = self.temp_dir / "test.TXT"
        txt_file.write_text("テストコンテンツ", encoding='utf-8')
        
        with patch('main.ScriptConverter') as mock_converter_class:
            mock_converter = MagicMock()
            output_file = self.temp_dir / "test.html"
            mock_converter.convert.return_value = output_file
            mock_converter_class.return_value = mock_converter
            
            sys.argv = ['main.py', str(txt_file)]
            main.main()
            
            mock_converter.convert.assert_called_once_with(txt_file)