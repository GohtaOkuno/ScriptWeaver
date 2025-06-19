#!/usr/bin/env python3
"""
ScriptWeaver: TRPGシナリオ自動変換ツール
.txt/.docx ファイルを構造化されたHTMLに変換します
"""

import sys
import os
from pathlib import Path
from src.converter import ScriptConverter


def main():
    """メインエントリーポイント"""
    if len(sys.argv) != 2:
        print("使用方法: python main.py <input_file>")
        print("対応形式: .txt, .docx")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    
    if not input_file.exists():
        print(f"エラー: ファイルが見つかりません: {input_file}")
        sys.exit(1)
    
    if input_file.suffix.lower() not in ['.txt', '.docx']:
        print(f"エラー: 対応していない形式です: {input_file.suffix}")
        print("対応形式: .txt, .docx")
        sys.exit(1)
    
    try:
        print(f"読み込み開始: {input_file}")
        converter = ScriptConverter()
        output_file = converter.convert(input_file)
        print(f"変換完了: {output_file}")
        
    except Exception as e:
        print(f"変換失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()