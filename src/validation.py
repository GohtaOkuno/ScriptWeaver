"""
ScriptWeaver バリデーションシステム
TRPGシナリオの記法を検証し、適切なフィードバックを提供
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
import re


class ValidationLevel(Enum):
    """バリデーション結果のレベル"""
    CRITICAL = "critical"    # 重大エラー（変換不可能）
    WARNING = "warning"      # 警告（改善推奨）
    INFO = "info"           # 情報（自動修正等）
    SUGGESTION = "suggestion"  # 提案（より良い書き方）


@dataclass
class ValidationResult:
    """バリデーション結果"""
    level: ValidationLevel
    message: str
    suggestion: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    code: Optional[str] = None  # エラーコード（例：SKILL_001）
    original_text: Optional[str] = None
    proposed_fix: Optional[str] = None


@dataclass
class ValidationConfig:
    """バリデーション設定"""
    strict_mode: bool = False
    trpg_system: str = "CoC6"
    custom_skills: List[str] = None
    warning_threshold: int = 10
    auto_fix: bool = True
    beginner_mode: bool = False  # 初心者向けモード
    
    def __post_init__(self):
        if self.custom_skills is None:
            self.custom_skills = []


class ValidationReport:
    """バリデーション結果の集約レポート"""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.summary: Dict[str, int] = {
            "critical": 0,
            "warning": 0, 
            "info": 0,
            "suggestion": 0
        }
    
    def add_result(self, result: ValidationResult):
        """結果を追加"""
        self.results.append(result)
        self.summary[result.level.value] += 1
    
    def has_errors(self) -> bool:
        """エラーがあるかチェック"""
        return self.summary["critical"] > 0
    
    def get_results_by_level(self, level: ValidationLevel) -> List[ValidationResult]:
        """指定レベルの結果のみ取得"""
        return [r for r in self.results if r.level == level]
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で出力"""
        return {
            "summary": self.summary,
            "results": [
                {
                    "level": r.level.value,
                    "message": r.message,
                    "suggestion": r.suggestion,
                    "line_number": r.line_number,
                    "column": r.column,
                    "code": r.code,
                    "original_text": r.original_text,
                    "proposed_fix": r.proposed_fix
                }
                for r in self.results
            ]
        }


class BaseValidator(ABC):
    """バリデータの基底クラス"""
    
    def __init__(self, config: ValidationConfig):
        self.config = config
    
    @abstractmethod
    def validate(self, text: str, line_number: int = None) -> List[ValidationResult]:
        """テキストをバリデーション"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """バリデータ名を取得"""
        pass
    
    def _create_result(
        self,
        level: ValidationLevel,
        message: str,
        suggestion: str = None,
        line_number: int = None,
        code: str = None,
        original_text: str = None,
        proposed_fix: str = None
    ) -> ValidationResult:
        """ValidationResult作成のヘルパー"""
        return ValidationResult(
            level=level,
            message=message,
            suggestion=suggestion,
            line_number=line_number,
            code=code,
            original_text=original_text,
            proposed_fix=proposed_fix
        )


class ValidationEngine:
    """バリデーションエンジンの中核クラス"""
    
    def __init__(self, config: ValidationConfig = None):
        self.config = config or ValidationConfig()
        self.validators: List[BaseValidator] = []
    
    def register_validator(self, validator: BaseValidator):
        """バリデータを登録"""
        self.validators.append(validator)
    
    def validate_document(self, content: str) -> ValidationReport:
        """ドキュメント全体をバリデーション"""
        report = ValidationReport()
        
        # 行ごとに分割して処理
        lines = content.split('\n')
        for line_number, line in enumerate(lines, 1):
            line_results = self.validate_line(line, line_number)
            for result in line_results:
                report.add_result(result)
        
        # ドキュメント全体の構造チェック
        document_results = self._validate_document_structure(content)
        for result in document_results:
            report.add_result(result)
        
        return report
    
    def validate_line(self, line: str, line_number: int) -> List[ValidationResult]:
        """行単位でバリデーション"""
        results = []
        
        for validator in self.validators:
            try:
                validator_results = validator.validate(line, line_number)
                results.extend(validator_results)
            except Exception as e:
                # バリデータエラーをCRITICALとして記録
                error_result = ValidationResult(
                    level=ValidationLevel.CRITICAL,
                    message=f"バリデータエラー ({validator.get_name()}): {str(e)}",
                    line_number=line_number,
                    code="VALIDATOR_ERROR"
                )
                results.append(error_result)
        
        return results
    
    def _validate_document_structure(self, content: str) -> List[ValidationResult]:
        """ドキュメント構造の検証"""
        results = []
        
        # 見出しの階層チェック
        heading_levels = []
        lines = content.split('\n')
        
        for line_number, line in enumerate(lines, 1):
            line = line.strip()
            
            # Markdown形式見出し
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                heading_levels.append((level, line_number))
            
            # 番号付き見出し
            elif re.match(r'^\d+\.', line):
                level = 1
                if re.match(r'^\d+-\d+\.', line):
                    level = 2
                elif re.match(r'^\d+-\d+-\d+\.', line):
                    level = 3
                heading_levels.append((level, line_number))
        
        # 見出し階層の妥当性チェック
        if heading_levels:
            prev_level = 0
            for level, line_number in heading_levels:
                if level > prev_level + 1:
                    results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        message=f"見出し階層が飛んでいます（レベル{prev_level}の次にレベル{level}）",
                        suggestion="段階的な見出し階層を推奨します",
                        line_number=line_number,
                        code="HEADING_HIERARCHY"
                    ))
                prev_level = level
        
        return results


# 共通の技能リスト（CoC6版）
COC6_SKILLS = [
    "目星", "聞き耳", "図書館", "説得", "信用", "隠れる", "忍び歩き",
    "鍵開け", "機械修理", "コンピュータ", "運転", "操縦", "心理学",
    "医学", "応急手当", "精神分析", "オカルト", "人類学", "考古学",
    "歴史", "自然史", "物理学", "化学", "生物学", "地質学", "天文学",
    "電気修理", "電子工学", "ナビゲート", "追跡", "写真術", "芸術",
    "クトゥルフ神話", "母国語", "他の言語", "回避", "キック", "組み付き",
    "こぶし", "頭突き", "投擲", "マーシャルアーツ", "剣道", "拳銃",
    "サブマシンガン", "ショットガン", "マシンガン", "ライフル"
]


class SkillValidator(BaseValidator):
    """技能記法バリデータ"""
    
    def get_name(self) -> str:
        return "SkillValidator"
    
    def validate(self, text: str, line_number: int = None) -> List[ValidationResult]:
        results = []
        
        # 【技能名】パターンを検索
        skill_pattern = r'【([^】]+)】'
        matches = re.finditer(skill_pattern, text)
        
        for match in matches:
            skill_name = match.group(1)
            
            # 修正値を除去して基本技能名を取得
            base_skill = re.sub(r'[+\-]\d+$', '', skill_name)
            base_skill = re.sub(r'or.+$', '', base_skill)  # or以降を除去
            
            # 技能名チェック
            all_skills = COC6_SKILLS + self.config.custom_skills
            
            if base_skill not in all_skills:
                # 類似技能名の提案
                suggestion = self._find_similar_skill(base_skill, all_skills)
                suggestion_text = f"【{suggestion}】でしょうか？" if suggestion else "標準技能名を確認してください"
                
                results.append(self._create_result(
                    level=ValidationLevel.WARNING if self.config.strict_mode else ValidationLevel.SUGGESTION,
                    message=f"未知の技能名です: {skill_name}",
                    suggestion=suggestion_text,
                    line_number=line_number,
                    code="SKILL_UNKNOWN",
                    original_text=match.group(0),
                    proposed_fix=f"【{suggestion}】" if suggestion else None
                ))
        
        return results
    
    def _find_similar_skill(self, input_skill: str, skill_list: List[str]) -> Optional[str]:
        """類似技能名を検索"""
        # 簡単な類似度計算（レーベンシュタイン距離の簡易版）
        best_match = None
        best_score = float('inf')
        
        for skill in skill_list:
            score = self._simple_distance(input_skill, skill)
            if score < best_score and score <= 2:  # 2文字以内の差
                best_score = score
                best_match = skill
        
        return best_match
    
    def _simple_distance(self, s1: str, s2: str) -> int:
        """簡易的な文字列距離計算"""
        if len(s1) > len(s2):
            s1, s2 = s2, s1
        
        distances = range(len(s1) + 1)
        for index2, char2 in enumerate(s2):
            new_distances = [index2 + 1]
            for index1, char1 in enumerate(s1):
                if char1 == char2:
                    new_distances.append(distances[index1])
                else:
                    new_distances.append(1 + min((distances[index1], distances[index1 + 1], new_distances[-1])))
            distances = new_distances
        
        return distances[-1]


class HeadingValidator(BaseValidator):
    """見出し記法バリデータ"""
    
    def get_name(self) -> str:
        return "HeadingValidator"
    
    def validate(self, text: str, line_number: int = None) -> List[ValidationResult]:
        results = []
        
        line = text.strip()
        
        # Markdown形式見出し
        if line.startswith('#'):
            heading_text = line.lstrip('#').strip()
            
            if not heading_text:
                results.append(self._create_result(
                    level=ValidationLevel.CRITICAL,
                    message="見出しが空です",
                    suggestion="見出しテキストを追加してください",
                    line_number=line_number,
                    code="HEADING_EMPTY"
                ))
            
            elif len(heading_text) > 100:
                results.append(self._create_result(
                    level=ValidationLevel.WARNING,
                    message="見出しが長すぎます（100文字以内推奨）",
                    suggestion="簡潔な見出しに修正することを推奨します",
                    line_number=line_number,
                    code="HEADING_TOO_LONG"
                ))
        
        # 番号付き見出し
        elif re.match(r'^\d+', line):
            if re.match(r'^\d+-\d+-\d+-', line):
                results.append(self._create_result(
                    level=ValidationLevel.INFO,
                    message="見出し階層が深すぎます（3階層まで推奨）",
                    suggestion="構造を見直すことを検討してください",
                    line_number=line_number,
                    code="HEADING_TOO_DEEP"
                ))
        
        return results


class DiceValidator(BaseValidator):
    """ダイス記法バリデータ"""
    
    def get_name(self) -> str:
        return "DiceValidator"
    
    def validate(self, text: str, line_number: int = None) -> List[ValidationResult]:
        results = []
        
        # ダイス記法パターン
        dice_pattern = r'(\d+)d(\d+)(?:([+\-])(\d+))?'
        matches = re.finditer(dice_pattern, text, re.IGNORECASE)
        
        for match in matches:
            dice_count = int(match.group(1))
            die_sides = int(match.group(2))
            modifier_sign = match.group(3)
            modifier_value = int(match.group(4)) if match.group(4) else 0
            
            # ダイス数チェック
            if dice_count > 100:
                results.append(self._create_result(
                    level=ValidationLevel.WARNING,
                    message="ダイス数が多すぎます",
                    suggestion="現実的なダイス数に調整してください",
                    line_number=line_number,
                    code="DICE_COUNT_HIGH"
                ))
            
            # 面数チェック
            standard_dice = [2, 3, 4, 6, 8, 10, 12, 20, 100]
            if die_sides not in standard_dice:
                results.append(self._create_result(
                    level=ValidationLevel.INFO,
                    message="一般的でないダイス面数です",
                    suggestion="標準的なダイス（d6, d10, d100等）の使用を推奨",
                    line_number=line_number,
                    code="DICE_SIDES_UNUSUAL"
                ))
            
            # 修正値チェック
            if modifier_value > 50:
                results.append(self._create_result(
                    level=ValidationLevel.WARNING,
                    message="修正値が大きすぎます",
                    suggestion="適切な修正値に調整してください",
                    line_number=line_number,
                    code="DICE_MODIFIER_HIGH"
                ))
        
        return results