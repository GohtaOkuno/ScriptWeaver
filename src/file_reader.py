"""
ファイル読み込み専用モジュール
.txt/.docx ファイルの読み込みとエンコーディング検出を担当
"""

from pathlib import Path
from typing import Optional
import chardet

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class FileReader:
    """ファイル読み込み専用クラス"""
    
    def __init__(self):
        # サポートするエンコーディングのリスト（優先順）
        self.supported_encodings = ['utf-8', 'shift_jis', 'cp932', 'euc-jp', 'iso-2022-jp']
    
    def read_file(self, file_path: Path) -> str:
        """ファイル形式に応じて適切な読み込み方法を選択"""
        if file_path.suffix.lower() == '.txt':
            return self._read_text_file(file_path)
        elif file_path.suffix.lower() == '.docx':
            return self._read_docx_file(file_path)
        else:
            raise ValueError(f"対応していない形式: {file_path.suffix}")
    
    def _read_text_file(self, file_path: Path) -> str:
        """テキストファイルを読み込み（エンコーディング自動検出）"""
        # まず chardet でエンコーディングを検出
        detected_encoding = self._detect_encoding_with_chardet(file_path)
        if detected_encoding:
            try:
                with open(file_path, 'r', encoding=detected_encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                pass
        
        # chardet が失敗した場合は従来の方法でフォールバック
        return self._read_with_fallback_encodings(file_path)
    
    def _detect_encoding_with_chardet(self, file_path: Path) -> Optional[str]:
        """chardetライブラリを使用してエンコーディングを検出"""
        try:
            with open(file_path, 'rb') as f:
                # ファイルサイズに応じてサンプルサイズを調整
                file_size = file_path.stat().st_size
                sample_size = min(file_size, 100000)  # 最大100KB
                raw_data = f.read(sample_size)
                
                if not raw_data:
                    return None
                
                result = chardet.detect(raw_data)
                
                # 信頼度が70%以上の場合のみ採用
                if result and result.get('confidence', 0) > 0.7:
                    encoding = result['encoding']
                    # chardetの結果をPythonのエンコーディング名に正規化
                    return self._normalize_encoding_name(encoding)
                    
        except Exception:
            # chardetライブラリがない場合やエラーの場合はNoneを返す
            pass
        
        return None
    
    def _normalize_encoding_name(self, encoding: str) -> Optional[str]:
        """chardetの結果をPythonの標準エンコーディング名に正規化"""
        if not encoding:
            return None
            
        encoding_lower = encoding.lower()
        
        # 一般的なマッピング
        mapping = {
            'shift_jis': 'shift_jis',
            'shift-jis': 'shift_jis',
            'sjis': 'shift_jis',
            'cp932': 'cp932',
            'windows-31j': 'cp932',
            'euc-jp': 'euc-jp',
            'eucjp': 'euc-jp',
            'iso-2022-jp': 'iso-2022-jp',
            'utf-8': 'utf-8',
            'utf8': 'utf-8',
        }
        
        return mapping.get(encoding_lower, encoding)
    
    def _read_with_fallback_encodings(self, file_path: Path) -> str:
        """フォールバックエンコーディングリストで順次試行"""
        last_error = None
        
        for encoding in self.supported_encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError as e:
                last_error = e
                continue
        
        # 全てのエンコーディングが失敗した場合
        raise ValueError(
            f"ファイルのエンコーディングを特定できませんでした: {file_path}\n"
            f"最後のエラー: {last_error}"
        )
    
    def _read_docx_file(self, file_path: Path) -> str:
        """Word文書を読み込み"""
        if not DOCX_AVAILABLE:
            raise ImportError(
                "python-docxがインストールされていません。\n"
                "pip install python-docx を実行してください。"
            )
        
        try:
            doc = Document(file_path)
            paragraphs = []
            
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    paragraphs.append(text)
            
            return '\n\n'.join(paragraphs)
            
        except Exception as e:
            raise IOError(f"Word文書の読み込みに失敗しました: {file_path}\nエラー: {e}")
    
    def get_supported_extensions(self) -> list[str]:
        """サポートしているファイル拡張子のリストを返す"""
        extensions = ['.txt']
        if DOCX_AVAILABLE:
            extensions.append('.docx')
        return extensions
    
    def is_supported_file(self, file_path: Path) -> bool:
        """ファイルがサポートされているかチェック"""
        return file_path.suffix.lower() in self.get_supported_extensions()