# KobitoKey_QWERTY

小人キーや人キーのケース、TypeSurfer各種の3DデータはReleasesよりダウンロード出来ます。
ダサい使い方はしないこと。


Layer 0 QWERTY
<img width="1280" height="690" alt="Image" src="images/layer0.png" />

Layer 1 NUMBER & Bluetooth
<img width="1280" height="690" alt="Image" src="images/layer1.png" />

Layer 2 SYMBOL & ARROW
<img width="1280" height="690" alt="Image" src="images/layer2.png" />

Layer 3 AUTO MOUSE
<img width="1280" height="690" alt="Image" src="images/layer3.png" />

## Bluetooth 接続手順

Bluetooth の操作キーは Layer 1(スペース長押し)の右手側にある(上の Layer 1 の図を参照)。
ホストと通信するのは左手側(セントラル)。右手側は左手側と自動でつながる。

### 新しい端末とペアリングする

1. 左右両方の電源を入れる
2. スペースを押しながら BT0〜BT4 のいずれかを押し、未使用のプロファイルを選ぶ
3. 端末の Bluetooth 設定で「KobitoKey」を追加する
4. LED が青に光れば接続完了(黄=接続待ち、赤=未接続)

### 接続先を切り替える

- スペース + BT0〜BT4 で切り替え。プロファイルごとに接続先を記憶し、最大5台まで登録できる

### ペアリングをやり直す

- スペース + CLR: 現在のプロファイルの登録だけを削除
- スペース + CLR ALL: 全プロファイルの登録を削除
- 削除したら端末側の Bluetooth 設定からも「KobitoKey」を削除してから、上の手順でペアリングし直す

### つながらないとき

- 無操作1時間でディープスリープに入る。適当なキーを押して復帰させる(トラックボールでは復帰しない)
- キー入力が届くのに動きがおかしい・左右がバラバラに動く場合は、GitHub Actions の成果物に含まれる
  settings_reset ファームウェアを左右両方に書き込んで設定を初期化し、通常のファームウェアを
  入れ直してからペアリングし直す(書き込みはリセットボタン2回押し → 現れる USB ドライブに
  UF2 ファイルをコピー)
