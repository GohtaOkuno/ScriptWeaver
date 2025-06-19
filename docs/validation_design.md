# ScriptWeaver バリデーション・エラーハンドリング設計

## 概要
TRPGシナリオの記法を厳密に検証し、適切なエラーメッセージとガイダンスを提供する機能の設計。

---

## 1. バリデーション機能の分類

### 1.1 構文レベル
- **記法パターンの正確性**
- **必須要素の存在確認**
- **構造的整合性のチェック**

### 1.2 意味レベル
- **TRPGとしての妥当性**
- **ゲームバランスの確認**
- **一貫性のチェック**

### 1.3 表示レベル
- **HTMLレンダリングの確認**
- **CSSスタイルの適用確認**
- **レスポンシブ対応の検証**

---

## 2. エラーレベル定義

### 2.1 CRITICAL（重大エラー）
- ファイル読み込み失敗
- 致命的な構文エラー
- HTML生成不可能

### 2.2 WARNING（警告）
- 非推奨記法の使用
- 曖昧な記法パターン
- パフォーマンス上の問題

### 2.3 INFO（情報）
- 自動修正の実行
- 代替記法の提案
- 最適化の提案

### 2.4 SUGGESTION（提案）
- より良い記法の推奨
- 追加機能の案内
- スタイル改善の提案

---

## 3. 具体的なバリデーションルール

### 3.1 見出し記法
```python
def validate_heading(text: str) -> ValidationResult:
    """見出し記法のバリデーション"""
    
    # CRITICAL: 空の見出し
    if not text.strip():
        return ValidationResult(
            level=Level.CRITICAL,
            message="見出しが空です",
            suggestion="見出しテキストを追加してください"
        )
    
    # WARNING: 長すぎる見出し
    if len(text) > 100:
        return ValidationResult(
            level=Level.WARNING,
            message="見出しが長すぎます（100文字以内推奨）",
            suggestion="簡潔な見出しに修正することを推奨します"
        )
    
    # INFO: 階層の深さ
    if text.count('-') > 2:
        return ValidationResult(
            level=Level.INFO,
            message="見出し階層が深すぎます（3階層まで推奨）",
            suggestion="構造を見直すことを検討してください"
        )
```

### 3.2 技能記法
```python
def validate_skill_notation(text: str) -> ValidationResult:
    """技能記法のバリデーション"""
    
    # 技能名の確認
    skill_names = [
        '目星', '聞き耳', '図書館', '説得', '信用', '隠れる',
        '忍び歩き', '鍵開け', '機械修理', 'コンピュータ'
        # ... 標準技能一覧
    ]
    
    if skill_name not in skill_names:
        return ValidationResult(
            level=Level.WARNING,
            message=f"未知の技能名です: {skill_name}",
            suggestion="標準技能名または正しいスペルを確認してください"
        )
```

### 3.3 ダイス記法
```python
def validate_dice_notation(text: str) -> ValidationResult:
    """ダイス記法のバリデーション"""
    
    # ダイス数の妥当性
    if dice_count > 100:
        return ValidationResult(
            level=Level.WARNING,
            message="ダイス数が多すぎます",
            suggestion="現実的なダイス数に調整してください"
        )
    
    # 面数の妥当性
    if die_sides not in [2, 3, 4, 6, 8, 10, 12, 20, 100]:
        return ValidationResult(
            level=Level.INFO,
            message="一般的でないダイス面数です",
            suggestion="標準的なダイス（d6, d10, d100等）の使用を推奨"
        )
```

---

## 4. バリデーション実装アーキテクチャ

### 4.1 ValidatorEngine
```python
class ValidationEngine:
    """バリデーションエンジンの中核クラス"""
    
    def __init__(self):
        self.validators = []
        self.results = []
    
    def register_validator(self, validator: BaseValidator):
        """バリデータの登録"""
        
    def validate_document(self, content: str) -> ValidationReport:
        """ドキュメント全体のバリデーション"""
        
    def validate_paragraph(self, paragraph: str) -> List[ValidationResult]:
        """段落レベルのバリデーション"""
```

### 4.2 専用バリデータクラス
```python
class HeadingValidator(BaseValidator):
    """見出し専用バリデータ"""
    
class SkillValidator(BaseValidator):
    """技能記法専用バリデータ"""
    
class DiceValidator(BaseValidator):
    """ダイス記法専用バリデータ"""
    
class TableValidator(BaseValidator):
    """表記法専用バリデータ"""
```

---

## 5. エラーレポート機能

### 5.1 レポート形式
```json
{
  "document_path": "scenario.txt",
  "validation_time": "2025-06-19T12:00:00Z",
  "summary": {
    "critical": 0,
    "warning": 3,
    "info": 5,
    "suggestion": 2
  },
  "results": [
    {
      "line": 15,
      "column": 10,
      "level": "WARNING",
      "message": "未知の技能名です: 目だま",
      "suggestion": "【目星】の誤記の可能性があります",
      "code": "SKILL_001"
    }
  ]
}
```

### 5.2 HTML出力での表示
```html
<div class="validation-report">
    <div class="warning">
        <span class="line-info">15行目:</span>
        <span class="message">未知の技能名です: 目だま</span>
        <span class="suggestion">【目星】の誤記の可能性があります</span>
    </div>
</div>
```

---

## 6. 段階的実装計画

### Phase 1: 基本バリデーション
- [ ] 構文エラーの検出
- [ ] 必須要素のチェック
- [ ] 基本的なエラーメッセージ

### Phase 2: 詳細バリデーション
- [ ] 技能名の辞書チェック
- [ ] ダイス記法の妥当性検証
- [ ] NPCステータスの整合性確認

### Phase 3: 高度な検証
- [ ] ゲームバランスのチェック
- [ ] シナリオ構造の分析
- [ ] 最適化提案機能

### Phase 4: インタラクティブ機能
- [ ] リアルタイムバリデーション
- [ ] 自動修正提案
- [ ] ガイド付き記法入力

---

## 7. 設定可能オプション

### 7.1 厳密度レベル
```python
ValidationConfig = {
    "strict_mode": False,        # 厳密モード
    "trpg_system": "CoC6",       # TRPGシステム
    "custom_skills": [],         # カスタム技能
    "warning_threshold": 10,     # 警告数の閾値
    "auto_fix": True            # 自動修正の有効化
}
```

### 7.2 出力形式オプション
- テキスト形式レポート
- JSON形式レポート  
- HTML埋め込み表示
- VSCode拡張連携

---

## 8. 期待される効果

### 8.1 品質向上
- 記法の統一化
- エラーの早期発見
- 一貫性のある出力

### 8.2 ユーザビリティ向上
- 明確なエラーメッセージ
- 建設的な修正提案
- 学習効果の促進

### 8.3 保守性向上
- コードの品質保証
- テストケースの自動生成
- 仕様変更への対応力