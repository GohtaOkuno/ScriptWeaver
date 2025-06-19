"""
バリデーションシステムとコンバーターの統合テスト
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from src.converter import ScriptConverter


class TestValidationIntegration:
    """バリデーション統合テスト"""
    
    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.converter = ScriptConverter(enable_validation=True)
    
    def teardown_method(self):
        """各テストメソッド実行後のクリーンアップ"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_converter_with_validation_enabled(self):
        """バリデーション有効化での変換テスト"""
        # テスト用ファイル作成
        test_file = self.temp_dir / "test_scenario.txt"
        content = """# テストシナリオ

## 概要
【目星】判定で手がかりを発見する。

## 問題のある記法
【目だま】判定で何かを見つける。
150d6のダメージを与える。
"""
        test_file.write_text(content, encoding='utf-8')
        
        # 変換実行
        output_file = self.converter.convert(test_file)
        
        # ファイルが生成されることを確認
        assert output_file.exists()
        html_content = output_file.read_text(encoding='utf-8')
        
        # 基本的なHTML構造を確認
        assert '<!DOCTYPE html>' in html_content
        assert '>テストシナリオ</h1>' in html_content
        assert 'coc-skill' in html_content
    
    def test_converter_with_validation_report_included(self):
        """バリデーションレポート込み変換テスト"""
        test_file = self.temp_dir / "test_with_errors.txt"
        content = """# エラーテストシナリオ

【目だま】判定で何かを発見。
【きき耳】で音を聞く。
1000d6のダメージ。
"""
        test_file.write_text(content, encoding='utf-8')
        
        # バリデーションレポート込みで変換
        output_file = self.converter.convert(test_file, include_validation_report=True)
        html_content = output_file.read_text(encoding='utf-8')
        
        # バリデーションレポートが含まれることを確認
        assert 'validation-report' in html_content
        assert '記法チェック結果' in html_content
        assert '提案' in html_content or '警告' in html_content
    
    def test_validate_only_function(self):
        """バリデーションのみ実行テスト"""
        test_file = self.temp_dir / "validation_only_test.txt"
        content = """# バリデーションテスト

【目だま】判定と【きき耳】判定。
150d6+100のダメージ。

###

長すぎる見出し: """ + "あ" * 120
        
        test_file.write_text(content, encoding='utf-8')
        
        # バリデーションのみ実行
        report = self.converter.validate_only(test_file)
        
        # レポート内容を確認
        assert len(report.results) > 0
        assert report.summary["suggestion"] > 0 or report.summary["warning"] > 0
        
        # 具体的なエラー内容を確認
        messages = [r.message for r in report.results]
        assert any("未知の技能名" in msg for msg in messages)
    
    def test_converter_without_validation(self):
        """バリデーション無効化での変換テスト"""
        converter_no_validation = ScriptConverter(enable_validation=False)
        
        test_file = self.temp_dir / "no_validation_test.txt"
        content = """# テストシナリオ
【目だま】判定。
"""
        test_file.write_text(content, encoding='utf-8')
        
        # バリデーション無効で変換
        output_file = converter_no_validation.convert(test_file)
        html_content = output_file.read_text(encoding='utf-8')
        
        # バリデーションレポートの内容が含まれないことを確認
        assert '記法チェック結果' not in html_content
        assert '📋 記法チェック結果' not in html_content
    
    def test_validation_with_various_errors(self):
        """様々なエラーパターンのテスト"""
        test_file = self.temp_dir / "various_errors.txt"
        content = """# テストシナリオ

## 技能エラー
【目だま】【きき耳】【としょかん】

## ダイスエラー  
200d7+200のダメージ

## 見出しエラー

###

#### 階層が飛んでいる見出し

####### 深すぎる見出し
"""
        test_file.write_text(content, encoding='utf-8')
        
        report = self.converter.validate_only(test_file)
        
        # 各種エラーが検出されることを確認
        messages = [r.message for r in report.results]
        
        # 技能名エラー
        skill_errors = [msg for msg in messages if "未知の技能名" in msg]
        assert len(skill_errors) >= 2  # 目だま、きき耳
        
        # ダイスエラー
        dice_errors = [msg for msg in messages if ("ダイス数" in msg or "一般的でない" in msg or "修正値" in msg)]
        assert len(dice_errors) >= 1
        
        # 見出しエラー
        heading_errors = [msg for msg in messages if ("見出しが空" in msg or "階層が飛んで" in msg)]
        assert len(heading_errors) >= 1
    
    def test_validation_suggestions(self):
        """提案機能のテスト"""
        test_file = self.temp_dir / "suggestion_test.txt"
        content = """# 提案テスト

【目だま】判定で発見。
【聞き耳】判定で聞く。
"""
        test_file.write_text(content, encoding='utf-8')
        
        report = self.converter.validate_only(test_file)
        
        # 提案が含まれることを確認
        suggestions = [r.suggestion for r in report.results if r.suggestion]
        assert any("目星" in suggestion for suggestion in suggestions)
    
    def test_skill_name_similarity(self):
        """技能名類似度判定のテスト"""
        test_cases = [
            ("【目だま】", "目星"),
            ("【きき耳】", "聞き耳"), 
            ("【図書かん】", "図書館"),
            ("【かくれる】", "隠れる")
        ]
        
        for input_skill, expected_suggestion in test_cases:
            test_file = self.temp_dir / f"similarity_test_{input_skill}.txt"
            content = f"# テスト\n\n{input_skill}判定"
            test_file.write_text(content, encoding='utf-8')
            
            report = self.converter.validate_only(test_file)
            
            # 適切な技能名が提案されることを確認
            suggestions = [r.suggestion for r in report.results if r.suggestion]
            assert any(expected_suggestion in str(suggestion) for suggestion in suggestions)
    
    def test_complex_scenario_validation(self):
        """複雑なシナリオのバリデーション"""
        test_file = self.temp_dir / "complex_scenario.txt"
        content = """# 複雑なテストシナリオ

## 概要
このシナリオは【目星】と【図書館】を使用します。

## 第1章：調査開始

### 1-1. 図書館での調査
【図書館】判定に成功すると、『古い記録』を発見する。
失敗時は1d3のSANc0/1の減少。

### 1-2. 現場調査  
【目星】判定で手がかりを発見。
【きき耳】で奇妙な音を聞く。

## NPC情報

田中一郎 (STR 12 CON 14 SIZ 10 INT 15 POW 13 DEX 11 HP 12 MP 13)
技能: 【説得】70 【信用】60 【隠れる】40
装備: 護身用ナイフ(1d4+DB) 携帯電話

時刻　| 出来事
------|-------
14:00 | 調査開始
16:00 | 手がかり発見
18:00 | 事件発生
"""
        test_file.write_text(content, encoding='utf-8')
        
        # バリデーション付きで変換
        output_file = self.converter.convert(test_file, include_validation_report=True)
        html_content = output_file.read_text(encoding='utf-8')
        
        # 正しい記法は問題なく変換
        assert '>複雑なテストシナリオ</h1>' in html_content
        assert 'coc-skill' in html_content
        assert 'coc-item' in html_content
        assert 'npc-status-block' in html_content
        assert 'scenario-table' in html_content
        
        # エラーがある場合はレポートに含まれる
        if 'validation-report' in html_content:
            assert '記法チェック結果' in html_content