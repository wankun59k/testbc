
# ワークフロー
## ノード間通信のライフサイクル
- ノードの追加

- マイニング
自分のブロックを積み上げる

- ブロックチェーンの承認
自分が登録しているノードに対してコンセンサスをとる

## 通貨取引
上記ネットワーク構築を行い、トランザクションを発行する

- トランザクションの発行
宛先(recipient)：宛先ハッシュ
数量(amount)　：数量※

※今回はマイニングとブロックチェーンのロジックを分離して考えるため
送信可能数量として、自分で積み上げたブロックを参照しない。

- マイニング

- ブロックチェーンの承認


# 実装（基本設計）

## ノードの追加
- /nodes/register
1件づつノード情報ipアドレスを登録する

## マイニング
- /mine
自分のブロックチェーンに新しいブロックを積み上げる

- 初期状態
タイムスタンプのみを持つノードを初期ノードとし、それに対して1つのブロックを積む。
このブロック以降についてトランザクションを内包することが可能。

- 新規ブロック

トランザクションが未発生なので送信者なし、受信者は自分のハッシュ、数量１で登録される。

- ブロック生成の考え方

index :ブロックの順序を一意にするためのラベル。
以下のハッシュ取得時に順序が変わると不正なハッシュとなるため。

timestamp :ブロック生成時刻 unixtime

proof :nonce のこと。つまり、このブロックが正当にマイニングされたことを示す数列。

prev_hash :前回までのブロックチェーンより生成されたハッシュ。
少しでも前回ブロックに改ざんがあると、このハッシュに差分が発生することで感知する。

transactions :このブロックが生成されてから発生した、ノード間での取引ログ。

## 承認
- /nodes/resolve
自分が登録しているノードに対して、それぞれのノードが所有しているブロックチェーンにアクセスする。
そのブロックチェーンの長さ、各ブロックの前回ハッシュ値を比較し齟齬がないことを確認する。
正当なブロックチェーンの中で最長なものを正当なブロックチェーンとみなす。

## トランザクションの発行
- /transaction
送信者に自身のハッシュ、受信者に相手のハッシュを登録し、トランザクションとして登録する。

# 改修よてち
- 通貨取引ジョブの自動化

- コンセンサスアルゴリズムの多重ループ処理の非同期化
（通貨取引の結果は後で受け取る）
