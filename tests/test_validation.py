"""
バリデーションシステムのテストケース
"""

import pytest
from src.validation import (
    ValidationLevel, ValidationResult, ValidationConfig, ValidationReport,
    ValidationEngine, SkillValidator, HeadingValidator, DiceValidator
)


class TestValidationResult:
    """ValidationResultクラスのテスト"""
    
    def test_creation(self):
        result = ValidationResult(
            level=ValidationLevel.WARNING,
            message="テストメッセージ",
            suggestion="修正提案",
            line_number=10,
            code="TEST_001"
        )
        
        assert result.level == ValidationLevel.WARNING
        assert result.message == "テストメッセージ"
        assert result.suggestion == "修正提案"
        assert result.line_number == 10
        assert result.code == "TEST_001"


class TestValidationReport:
    """ValidationReportクラスのテスト"""
    
    def test_empty_report(self):
        report = ValidationReport()
        assert len(report.results) == 0
        assert not report.has_errors()
        assert report.summary["critical"] == 0
    
    def test_add_results(self):
        report = ValidationReport()
        
        # WARNING追加
        warning = ValidationResult(ValidationLevel.WARNING, "警告メッセージ")
        report.add_result(warning)
        
        # CRITICAL追加
        critical = ValidationResult(ValidationLevel.CRITICAL, "重大エラー")
        report.add_result(critical)
        
        assert len(report.results) == 2
        assert report.has_errors()  # CRITICALがあるためTrue
        assert report.summary["warning"] == 1
        assert report.summary["critical"] == 1
    
    def test_get_results_by_level(self):
        report = ValidationReport()
        
        warning1 = ValidationResult(ValidationLevel.WARNING, "警告1")
        warning2 = ValidationResult(ValidationLevel.WARNING, "警告2")
        info = ValidationResult(ValidationLevel.INFO, "情報")
        
        report.add_result(warning1)
        report.add_result(warning2)
        report.add_result(info)
        
        warnings = report.get_results_by_level(ValidationLevel.WARNING)
        assert len(warnings) == 2
        
        infos = report.get_results_by_level(ValidationLevel.INFO)
        assert len(infos) == 1
    
    def test_to_dict(self):
        report = ValidationReport()
        result = ValidationResult(
            level=ValidationLevel.WARNING,
            message="テスト",
            line_number=5
        )
        report.add_result(result)
        
        dict_result = report.to_dict()
        assert "summary" in dict_result
        assert "results" in dict_result
        assert dict_result["summary"]["warning"] == 1
        assert len(dict_result["results"]) == 1


class TestValidationConfig:
    """ValidationConfigクラスのテスト"""
    
    def test_default_config(self):
        config = ValidationConfig()
        assert not config.strict_mode
        assert config.trpg_system == "CoC6"
        assert config.custom_skills == []
        assert config.warning_threshold == 10
        assert config.auto_fix
        assert not config.beginner_mode
    
    def test_custom_config(self):
        config = ValidationConfig(
            strict_mode=True,
            custom_skills=["カスタム技能"],
            beginner_mode=True
        )
        assert config.strict_mode
        assert "カスタム技能" in config.custom_skills
        assert config.beginner_mode


class TestSkillValidator:
    """SkillValidatorクラスのテスト"""
    
    def setup_method(self):
        self.config = ValidationConfig()
        self.validator = SkillValidator(self.config)
    
    def test_valid_skill(self):
        """正しい技能名のテスト"""
        text = "【目星】判定で手がかりを発見"
        results = self.validator.validate(text, 1)
        
        # 標準技能名なのでエラーなし
        assert len(results) == 0
    
    def test_unknown_skill(self):
        """未知の技能名のテスト"""
        text = "【目だま】判定で何かを見つける"
        results = self.validator.validate(text, 1)
        
        assert len(results) == 1
        result = results[0]
        assert result.level == ValidationLevel.SUGGESTION  # 非厳密モード
        assert "未知の技能名" in result.message
        assert "目星" in result.suggestion  # 類似技能名を提案
    
    def test_skill_with_modifier(self):
        """修正値付き技能のテスト"""
        text = "【目星-20】の困難な判定"
        results = self.validator.validate(text, 1)
        
        # 修正値があっても基本技能名が正しければOK
        assert len(results) == 0
    
    def test_skill_with_or(self):
        """or技能のテスト"""
        text = "【機械修理orコンピュータ】で判定"
        results = self.validator.validate(text, 1)
        
        # 複合技能でも基本部分が正しければOK
        assert len(results) == 0
    
    def test_strict_mode(self):
        """厳密モードのテスト"""
        self.config.strict_mode = True
        validator = SkillValidator(self.config)
        
        text = "【目だま】判定"
        results = validator.validate(text, 1)
        
        assert len(results) == 1
        assert results[0].level == ValidationLevel.WARNING  # 厳密モードではWARNING
    
    def test_custom_skills(self):
        """カスタム技能のテスト"""
        self.config.custom_skills = ["カスタム技能"]
        validator = SkillValidator(self.config)
        
        text = "【カスタム技能】を使用"
        results = validator.validate(text, 1)
        
        # カスタム技能として登録されているのでエラーなし
        assert len(results) == 0


class TestHeadingValidator:
    """HeadingValidatorクラスのテスト"""
    
    def setup_method(self):
        self.config = ValidationConfig()
        self.validator = HeadingValidator(self.config)
    
    def test_valid_heading(self):
        """正しい見出しのテスト"""
        text = "# シナリオタイトル"
        results = self.validator.validate(text, 1)
        assert len(results) == 0
    
    def test_empty_heading(self):
        """空の見出しのテスト"""
        text = "###"
        results = self.validator.validate(text, 1)
        
        assert len(results) == 1
        result = results[0]
        assert result.level == ValidationLevel.CRITICAL
        assert "見出しが空" in result.message
    
    def test_long_heading(self):
        """長すぎる見出しのテスト"""
        long_title = "あ" * 150  # 150文字の見出し
        text = f"# {long_title}"
        results = self.validator.validate(text, 1)
        
        assert len(results) == 1
        result = results[0]
        assert result.level == ValidationLevel.WARNING
        assert "長すぎます" in result.message
    
    def test_deep_numbered_heading(self):
        """深すぎる番号見出しのテスト"""
        text = "1-2-3-4. 深すぎる見出し"
        results = self.validator.validate(text, 1)
        
        assert len(results) == 1
        result = results[0]
        assert result.level == ValidationLevel.INFO
        assert "階層が深すぎます" in result.message


class TestDiceValidator:
    """DiceValidatorクラスのテスト"""
    
    def setup_method(self):
        self.config = ValidationConfig()
        self.validator = DiceValidator(self.config)
    
    def test_valid_dice(self):
        """正しいダイス記法のテスト"""
        text = "1d6+2のダメージを受ける"
        results = self.validator.validate(text, 1)
        assert len(results) == 0
    
    def test_high_dice_count(self):
        """ダイス数が多すぎるテスト"""
        text = "150d6でダメージ計算"
        results = self.validator.validate(text, 1)
        
        assert len(results) == 1
        result = results[0]
        assert result.level == ValidationLevel.WARNING
        assert "ダイス数が多すぎます" in result.message
    
    def test_unusual_dice_sides(self):
        """珍しい面数のダイスのテスト"""
        text = "1d7で判定"  # 7面ダイスは一般的でない
        results = self.validator.validate(text, 1)
        
        assert len(results) == 1
        result = results[0]
        assert result.level == ValidationLevel.INFO
        assert "一般的でない" in result.message
    
    def test_high_modifier(self):
        """修正値が大きすぎるテスト"""
        text = "1d6+100の異常な修正"
        results = self.validator.validate(text, 1)
        
        assert len(results) == 1
        result = results[0]
        assert result.level == ValidationLevel.WARNING
        assert "修正値が大きすぎます" in result.message


class TestValidationEngine:
    """ValidationEngineクラスのテスト"""
    
    def setup_method(self):
        self.config = ValidationConfig()
        self.engine = ValidationEngine(self.config)
        
        # バリデータを登録
        self.engine.register_validator(SkillValidator(self.config))
        self.engine.register_validator(HeadingValidator(self.config))
        self.engine.register_validator(DiceValidator(self.config))
    
    def test_validate_single_line(self):
        """単一行のバリデーション"""
        line = "【目星】判定で1d6のダメージ"
        results = self.engine.validate_line(line, 1)
        
        # 正しい記法なのでエラーなし
        assert len(results) == 0
    
    def test_validate_line_with_errors(self):
        """エラーがある行のバリデーション"""
        line = "【目だま】判定で150d6のダメージ"
        results = self.engine.validate_line(line, 1)
        
        # 技能名エラーとダイス数エラーで2つ
        assert len(results) == 2
    
    def test_validate_document(self):
        """ドキュメント全体のバリデーション"""
        content = """# シナリオタイトル

## 概要
【目星】判定で手がかりを発見する。

### 詳細
【目だま】判定で1d100+5の結果を得る。
"""
        
        report = self.engine.validate_document(content)
        
        # 技能名エラーが1つあるはず
        assert report.summary["suggestion"] >= 1  # 目だま→目星の提案
        assert not report.has_errors()  # CRITICALエラーはない
    
    def test_heading_hierarchy_validation(self):
        """見出し階層のバリデーション"""
        content = """# タイトル
### 階層が飛んでいる見出し
"""
        
        report = self.engine.validate_document(content)
        
        # 階層エラーがあるはず
        hierarchy_warnings = [r for r in report.results if "階層が飛んで" in r.message]
        assert len(hierarchy_warnings) >= 1
    
    def test_empty_document(self):
        """空のドキュメントのテスト"""
        content = ""
        report = self.engine.validate_document(content)
        
        # 空でもエラーにはならない
        assert not report.has_errors()
        assert len(report.results) == 0