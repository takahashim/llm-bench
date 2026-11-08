Mastodon API Ruby Gemを使ってMastodonのインスタンスに投稿するCLIのサンプルです。

## コード

[コード]

Gemfileは以下。

[コード]

## 使い方

Dotenvを使っていて、カレントディレクトリの`.env`ファイルに書かれている情報を環境変数として参照します。また、環境変数`MASTODON_URL`,`MASTODON_CLIENT_ID`,`MASTODON_CLIENT_SECRET`,`MASTODON_ACCESS_TOKEN`が設定されていない場合、`.env`ファイルに書き込みます。

.envファイルもなく、環境変数も設定されていない場合に実行すると、以下のようにMastodonインスタンスのURL、ID、パスワード、メッセージを聞いてきて、結果を出力します。

[コード]

2回めに実行すると、上記の.envに保存された値を利用して、

[コード]

書き込むメッセージは引数でも渡せます。

[コード]

.envの中身は以下のようになります（このトークンは削除済みです）。

[コード]

その他使用している環境変数は以下です。

|環境変数名|内容|
|--------------|----------------------|
| MASTODON_URL | MastodonインスタンスのURL|
| MASTODON_CLIENT_ID |クライアントID|
| MASTODON_CLIENT_SECRET |クライアントSECRET|
| MASTODON_ACCESS_TOKEN |アクセストークン|
| MASTODON_SCOPES | スコープ(read, write, followのうち必要なものをスペース区切りで) |
| MASTODON_APP_NAME |クライアントアプリ名(設定画面の「認証済みアプリ」で表示される)|

## 補足説明

Mastodon::REST::Client#create_appでclient_idとclient_secretを取得してからOAuth2::Clientのパスワード認証（？ RFC6749でいうところのResource Owner Password Credentials Grant）でアクセストークンを取得しています。最初それがよく分からなくて、Mastodon::REST::Clientでどうやってやればいいのか悩んでいましたが、そこはOAuth2を使うのが正解なのではという結論に達しました。

アクセストークンを取得したあとは改めてMastodon::REST::Client.newすると、今度は普通にAPIを叩けるようになります。それぞれのAPIの使い方は http://www.rubydoc.info/github/tootsuite/mastodon-api/master をどうぞ。

## 参考

* http://qiita.com/shindyu/items/6a1f0c567774516f07da
* https://github.com/tootsuite/documentation/tree/master/Using-the-API
* http://www.rubydoc.info/github/tootsuite/mastodon-api/master
* http://www.rubydoc.info/github/intridea/oauth2
* https://murashun.jp/blog/20150920-01.html
