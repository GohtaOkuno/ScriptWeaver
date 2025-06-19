# ScriptWeaver API リファレンス

## 概要

ScriptWeaver は TRPG シナリオを .txt/.docx ファイルから美しい HTML に変換するツールです。

## クイックスタート

### 基本的な使用方法

```python
from src.converter_refactored import ScriptConverter
from pathlib import Path

# 基本的な変換
converter = ScriptConverter()
output_file = converter.convert(Path("scenario.txt"))
print(f"変換完了: {output_file}")
```

### バリデーション付き変換

```python
# バリデーションレポート込みで変換
output_file = converter.convert(
    Path("scenario.txt"), 
    include_validation_report=True
)
```

### バリデーションのみ実行

```python
# 変換せずにバリデーションのみ
report = converter.validate_only(Path("scenario.txt"))
print(f"エラー数: {report.summary['critical']}")
```

## メインクラス

### ScriptConverter

TRPGシナリオ変換のメインコントローラークラス。

#### コンストラクタ

```python
ScriptConverter(config: Optional[ScriptWeaverConfig] = None)
```

**パラメータ:**
- `config`: 設定オブジェクト。未指定時はデフォルト設定を使用。

#### メソッド

##### convert()

```python
convert(input_file: Path, include_validation_report: bool = False) -> Path
```

入力ファイルをHTMLに変換します。

**パラメータ:**
- `input_file`: 変換対象ファイル (.txt または .docx)
- `include_validation_report`: バリデーションレポートをHTMLに含めるか

**戻り値:**
- `Path`: 生成されたHTMLファイルのパス

**例外:**
- `ValueError`: 対応していないファイル形式
- `IOError`: ファイル読み込み/書き込みエラー

**使用例:**
```python
converter = ScriptConverter()

# 基本変換
output = converter.convert(Path("scenario.txt"))

# バリデーション付き変換
output = converter.convert(
    Path("scenario.txt"), 
    include_validation_report=True
)
```

##### validate_only()

```python
validate_only(input_file: Path) -> ValidationReport
```

ファイルをバリデーションのみ実行（変換なし）。

**パラメータ:**
- `input_file`: 検証対象ファイル

**戻り値:**
- `ValidationReport`: バリデーション結果

**例外:**
- `RuntimeError`: バリデーション機能が無効化されている
- `ValueError`: 対応していないファイル形式

**使用例:**
```python
report = converter.validate_only(Path("scenario.txt"))

# 結果の確認
print(f"重大エラー: {report.summary['critical']}")
print(f"警告: {report.summary['warning']}")

# 詳細結果
for result in report.results:
    print(f"{result.line_number}行目: {result.message}")
```

##### get_supported_formats()

```python
get_supported_formats() -> List[str]
```

サポートしているファイル形式の一覧を取得。

**戻り値:**
- `List[str]`: サポートファイル拡張子のリスト（例: ['.txt', '.docx']）

##### update_config()

```python
update_config(**kwargs)
```

設定を動的に更新。

**パラメータ:**
- `**kwargs`: 更新する設定項目

**使用例:**
```python
converter.update_config(
    enable_validation=False,
    strict_mode=True
)
```

## 設定クラス

### ScriptWeaverConfig

ScriptWeaver の全体設定を管理するデータクラス。

#### 主要な設定項目

##### ファイル処理設定
- `default_encoding: str = 'utf-8'` - デフォルトエンコーディング
- `supported_encodings: List[str]` - サポートエンコーディング一覧
- `max_file_size: int = 50MB` - 最大ファイルサイズ
- `encoding_confidence_threshold: float = 0.7` - エンコーディング検出の信頼度閾値

##### バリデーション設定
- `enable_validation: bool = True` - バリデーション有効化
- `strict_mode: bool = False` - 厳密モード
- `trpg_system: str = "CoC6"` - TRPGシステム
- `custom_skills: List[str]` - カスタム技能リスト
- `beginner_mode: bool = False` - 初心者モード

##### HTML生成設定
- `html_title: str = 'TRPGシナリオ'` - HTMLタイトル
- `include_toc: bool = True` - 目次生成
- `toc_title: str = '目次'` - 目次タイトル

#### ファクトリメソッド

##### create_default()

```python
@classmethod
create_default() -> ScriptWeaverConfig
```

デフォルト設定を作成。

##### create_beginner_mode()

```python
@classmethod
create_beginner_mode() -> ScriptWeaverConfig
```

初心者向け設定を作成（エラー判定を緩く、自動修正を有効）。

##### create_strict_mode()

```python
@classmethod
create_strict_mode() -> ScriptWeaverConfig
```

厳密モード設定を作成（エラー判定を厳しく）。

**使用例:**
```python
from src.config import ScriptWeaverConfig
from src.converter_refactored import ScriptConverter

# 初心者向け設定
beginner_config = ScriptWeaverConfig.create_beginner_mode()
converter = ScriptConverter(beginner_config)

# 厳密モード設定
strict_config = ScriptWeaverConfig.create_strict_mode()
converter = ScriptConverter(strict_config)
```

## バリデーション

### ValidationReport

バリデーション結果を格納するクラス。

#### 属性
- `results: List[ValidationResult]` - 個別の検証結果
- `summary: Dict[str, int]` - エラーレベル別の集計

#### メソッド

##### has_errors()

```python
has_errors() -> bool
```

重大エラーがあるかチェック。

##### get_results_by_level()

```python
get_results_by_level(level: ValidationLevel) -> List[ValidationResult]
```

指定レベルの結果のみ取得。

### ValidationResult

個別のバリデーション結果。

#### 属性
- `level: ValidationLevel` - エラーレベル（CRITICAL/WARNING/INFO/SUGGESTION）
- `message: str` - エラーメッセージ
- `suggestion: Optional[str]` - 修正提案
- `line_number: Optional[int]` - 行番号
- `proposed_fix: Optional[str]` - 修正案

## ファクトリ関数

### create_converter()

```python
create_converter(enable_validation: bool = True) -> ScriptConverter
```

旧API互換のためのファクトリ関数。

### create_beginner_converter()

```python
create_beginner_converter() -> ScriptConverter
```

初心者向けコンバータを作成。

### create_strict_converter()

```python
create_strict_converter() -> ScriptConverter
```

厳密モードコンバータを作成。

## TRPG記法サポート

### 対応記法

#### 見出し
```
# メインタイトル
## 章タイトル
### セクション

1. 番号付き見出し
2-1. サブ見出し
2-1-1. 詳細見出し
```

#### CoC6版専用記法
```
【目星】                  # 技能判定
【聞き耳-20】            # 修正値付き判定
『古い日記』              # アイテム・文書
1d6                     # ダイス
2d10+3                  # 修正付きダイス
SANc1/1d4               # SAN減少
「こんにちは」           # 会話文
```

#### 構造要素
```
# 表
項目1 | 項目2 | 項目3
------|------|------
内容1 | 内容2 | 内容3

# 定義リスト
◆ 用語：説明
◆ 別用語：別説明

# 箇条書き
・ 項目1
・ 項目2

# セクション区切り
==================
------------------
```

#### NPCステータス
```
田中一郎 (STR 12 CON 14 SIZ 10 INT 15 POW 13 DEX 11 HP 12 MP 13)
技能: 〈説得〉70 〈信用〉60
装備: ナイフ(1d4+DB) 拳銃(1d10)
```

## エラーハンドリング

### 一般的な例外

#### ValueError
- 対応していないファイル形式
- エンコーディング検出失敗
- 厳密モードでの重大エラー

#### IOError
- ファイル読み込み失敗
- ファイル書き込み失敗

#### RuntimeError
- バリデーション機能が無効時のvalidate_only()呼び出し

### 例外処理の例

```python
from src.converter_refactored import ScriptConverter
from pathlib import Path

converter = ScriptConverter()

try:
    output = converter.convert(Path("scenario.txt"))
    print(f"変換成功: {output}")
    
except ValueError as e:
    print(f"入力エラー: {e}")
    
except IOError as e:
    print(f"ファイルエラー: {e}")
    
except Exception as e:
    print(f"予期しないエラー: {e}")
```

## パフォーマンス

### 最適化ポイント

1. **正規表現の事前コンパイル**: パターンマッチングが高速化
2. **LRUキャッシュ**: 見出しID生成などでキャッシュを活用
3. **エンコーディング検出の最適化**: chardetで高精度検出
4. **モジュラー設計**: 必要な機能のみロード

### パフォーマンス指標

- **小さなファイル** (〜10KB): 0.1秒未満
- **中規模ファイル** (〜100KB): 0.5秒未満  
- **大きなファイル** (〜1MB): 2秒未満

## 拡張性

### カスタムバリデータの追加

```python
from src.validation import BaseValidator, ValidationResult, ValidationLevel

class CustomValidator(BaseValidator):
    def get_name(self) -> str:
        return "CustomValidator"
    
    def validate(self, text: str, line_number: int = None) -> List[ValidationResult]:
        results = []
        # カスタムバリデーション処理
        return results

# 登録
converter = ScriptConverter()
if converter.validation_engine:
    converter.validation_engine.register_validator(CustomValidator(config))
```

### カスタムプロセッサの作成

ContentProcessor を継承してカスタム処理を実装可能。

## トラブルシューティング

### よくある問題

#### 1. エンコーディングエラー
```
ValueError: ファイルのエンコーディングを特定できませんでした
```

**解決方法:**
- ファイルを UTF-8 で保存し直す
- chardet ライブラリが正しくインストールされているか確認

#### 2. バリデーションエラー
```
RuntimeError: バリデーション機能が無効化されています
```

**解決方法:**
```python
# バリデーション有効化
converter.update_config(enable_validation=True)
```

#### 3. 重大エラーで変換停止
```
ValueError: バリデーションで重大エラーが検出されました
```

**解決方法:**
```python
# 厳密モードを無効化
converter.update_config(strict_mode=False)
```

## 参考資料

- [TRPG記法仕様書](trpg_notation_spec.md)
- [バリデーション設計](validation_design.md)
- [記述ガイド](writing_guide.md)