# KobitoKey_QWERTY

KobitoKey(4行×10列・左右分割キーボード)の ZMK ファームウェア設定リポジトリ。

- `config/KobitoKey.keymap` — キーマップ本体(レイヤー定義・コンボ定義)
- `config/boards/shields/KobitoKey/` — シールド定義(マトリクス・物理レイアウト)
- `images/layer*.png` — README に載せる各レイヤーのキーマップ図
- `scripts/generate_keymap_images.py` — キーマップから上記画像を自動生成するスクリプト
- ファームウェアのビルドは GitHub Actions(`.github/workflows/build.yml`)で行う

## キーマップ変更時の必須ワークフロー

`config/KobitoKey.keymap` を変更したら、**必ず画像も再生成する**こと:

```bash
python3 scripts/generate_keymap_images.py
```

- 生成された `images/layer*.png` と `images/.keymap-hash` をキーマップと一緒にコミットする。
- `.keymap-hash` はキーマップ+生成スクリプトのハッシュ。CI
  (`.github/workflows/keymap-images.yml`)が照合し、画像を更新し忘れたまま
  push するとチェックが失敗する。
- レイヤー構成を変えた場合は `README.md` のレイヤー見出し(例: `Layer 2 SYMBOL & Bluetooth`)も
  合わせて更新する。

### スクリプトの依存

Pillow のみ。未導入なら:

```bash
python3 -m venv .venv && .venv/bin/pip install pillow
.venv/bin/python scripts/generate_keymap_images.py
```

### 新しいキーコード・ビヘイビアを使ったとき

キーマップに表示ラベル未定義のキーコード/ビヘイビアを追加すると、スクリプトは
エラーで停止する(画像の抜け漏れ防止のための意図的な挙動)。
`scripts/generate_keymap_images.py` の `KEY_LABELS` / `MOD_SUBLABELS` /
`binding_label()` に表示ラベルを追加してから再実行する。

レイヤーのタイトル表記は `LAYER_TITLES`、特定キーだけラベルを消す等の
デザイン上の例外は `LABEL_OVERRIDES` で管理している。
