※タイトル変えました。

2016年4月29日、Re:VIEWのメジャーバージョンアップ版である Re:VIEW 2.0 がリリースされました。

Re:VIEW 2.0とRe:VIEW 1.xとは細かい非互換がいくつかあります。そのため、1.7.x以前のRe:VIEWで使っていた文書がそのままではビルドできないことがあります。

本稿では、1.7以前と2.0との違いと、その対応方法について説明します。

#:fire: 奥付の「発行所」が「印刷所」になってしまう

config.ymlの`prt`の意味が代わりました（もともとがバグっていたのでした…申し訳ございません）。`prt`は「発行所」ではなく「印刷所」になりました。「発行所」は`pbl`になります。config.ymlを変更してください。

1.7では互換用のコードを入れていたのですが、2.0では削除されています。

むりやり元の設定で使い続けるには、locale.ymlを以下のようにします。

[コード]

#:fire: texdocumentclassを指定している文書がエラーになる

2.0のPDFMaker(LATEXBuilder)が標準で使用するLaTeX処理系は、pLaTeXからupLaTeXに変更しました。
upLaTeXはUnicode文字が標準で使える等便利な点もあります。しかし、スタイルの指定が異なるため、config.ymlで`texdocumentclass:`を指定していた場合は修正する必要があります（`texdocumentclass:`を指定していない場合はそのまま使えます）。

`jsbook`を使っている場合、簡単な置き換え方法としては、以下の方法があります。

* texdocumentclassの引数の2番目の要素の末尾に「,uplatex」を追加して、uplatexを指定する

修正例は以下のようになります。

[コード]

upLaTeXではなく、あくまでpLaTeXを使いたい、という方は、config.ymlに`texcommand:`の設定を追加します。

[コード]

これで2.0でもupLaTeXではなくpLaTeXが使われるようになります。

#:warning:  「config.ymlに`review_version:`の指定がない」という警告が出る

これは必須ではないのですが、2.0以降ではRe:VIEWのバージョンをconfig.ymlに記述できるようになりました。
ビルドする際、メジャーバージョンが異なっていた場合、警告が表示されます。

Re:VIEWの2.0.xを使う場合、config.ymlの冒頭に以下のような記述を追加してください。

[コード]

今後はこのバージョン指定を使って警告等を出したいのですが、そんな警告は見たくない、という方は以下のように指定します。

[コード]

# :fire: layouts/layout.*.erb を使用している文書がエラーになる

Re:VIEW 2.0ではテンプレートエンジンとしてReVIEW::TemplateというERbラッパーを統一的に使っています。ReVIEW::Templateでは、Ruby on RailsやSinatraのテンプレート同様、「@」で始まるインスタンス変数を渡すように変更されています。
テンプレートは通常、Re:VIEW内部で使われるもので、変更があってもユーザには影響は（あまり）ありません。しかし、テンプレートを独自に修正したいという要望に応えるため、layouts/ディレクトリ以下にカスタムのテンプレートファイルを設置することができます。この場合、テンプレートファイルに互換性がないため、エラーになります。

## layout.html.erb、layout.erbの場合

1.xの中でも古いバージョンのRe:VIEWでは、layout.erbというファイル名を使っていたことがあります。
現在の標準はlayout.html.erbになります。こちらにリネームしてください。

また、テンプレートも変更になっています。
1.xのRe:VIEWでは、テンプレートへの情報引き渡し用に、`title`や`body`というローカル変数が使われていました。
これらは`@title`、`@body`というインスタンス変数に変更され、さらに新しい変数がいくつか追加されています。

修正手順は以下のようになります。

1. https://raw.githubusercontent.com/kmuto/review/master/templates/html/layout-html5.html.erb のファイルを持ってきて、layout.html.erbという名前にする
2. 以前のlayout.html.erbまたはlayout.erbを元に、layout.html.erbを編集する
3. 古いファイルを削除し、編集したlayout.html.erbを文書レポジトリの layouts/ ディレクトリ下にコピーする

## layout.tex.erbの場合

1.xのRe:VIEWでは、テンプレートへの情報引き渡し用に、
`documentclassoption`、`documentclass`、そして`values`というローカル変数が使われていました。

これらは`@documentclassoption`、`@documentclass`、`@config`というインスタンス変数に変更されました。

修正手順は以下のようになります。

 1. https://raw.githubusercontent.com/kmuto/review/master/templates/latex/layout.tex.erb のファイルを持ってくる
 2. 以前のlayout.tex.erbを元に、layout.tex.erbを編集する
 3. 編集したlayout.tex.erbを文書レポジトリの layouts/ ディレクトリ下にコピーする（以前のlayout.tex.erbに上書きする ）

なお、values変数のうち、`values["pre_str"]`、`values["chap_str"]`、`values["post_str"]`は`@input_files["PREDEF"]`、`@input_files["CHAPS"]`、そして`@input_files["APPENDIX"]`と`@input_files["POSTDEF"]`になりました。それ以外のは、概ね`@config["foo"]`に変更されています。

# :fire: config.yaml、locale.yamlという名前にしているとエラーになる

設定ファイルの標準ファイル名は`config.yaml`ではなく`config.yml`で統一するようになりました。
`config.yaml`という名前にしている方は`config.yml`に変更してください。

同様に、ローカライズ用のファイルも`locale.yml`に統一されました。`locale.yaml`という名前にしている場合は`locale.yml`に修正してください。

# :fire: config.ymlで`pubhistory`、`coverfile`等を使っている文書がエラーになる

config.ymlの設定項目の名前は1.6.xの段階ですでに変わりつつありましたが、2.0で標準が変更になりました。

* `coverfile:`は`cover:`にします。`cover:`は`<body>`要素内のみではなくHTML全体になります。
* `pubhistory:`は`history:`にします。`history`は配列の配列になります。
* `backcoverfile:`は`backcover:`にします。
* `titlepagefile`は`titlefile:`にします。

# :fire: review-ext.rbを使用している文書がエラーになる

`review-ext.rb`は便利な半面、細かい内部仕様が変更になるだけでエラーが発生しやすくなってしまっています。
もっとも、ふつうの人は`review-ext.rb`は使わない(そもそもRe:VIEWのソースコードが読めてRubyが書ける人しか`review-ext.rb`は使えない)とは思います。
が、いろいろあって`review-ext.rb`を使っている方で、エラーが出てしまった場合は、`lib/review/*builder.rb`を参考に修正をお願いします :bow:

# :fire: config.ymlで`epubversion:`、`htmlversion:`を指定していない文書をEPUBに変換するとエラーになる

標準で生成するEPUBのバージョンがEPUB 2からEPUB 3に変更になりました。何も指定しないとEPUB 3のファイルになります。

EPUB 2を使いたい場合は、config.ymlに以下のような指定を追加してください。

[コード]

## 余談: `htmlext:`について

これは非互換ではないのですが、次の例のように`htmlext:`を直下と`epubmaker:`以下に書くと、EPUBとそれ以外で使い分けができます。

[コード]

このようにすれば、EPUBでは*.xhtml、それ以外では*.htmlになります。

最近のEPUBでは*.xhtmlにしないとepubcheckでエラーになるため、拡張子はxhtmlにしたいところです。一方、Re:VIEW 2.0ではwebmakerというWebサイト向け静的HTMLを生成するコマンドができたので、こちらの拡張子はhtmlにしたい。この両立のための設定です。

# :warning: CHAPSファイルやPREDEFファイルが廃止になる

これはまだ警告を出していない（出したらテストが異常にうるさくなり、テストを修正しきれなかった……）のですが、Re:VIEW 1.3以降ではCHAPSファイルやPREDEFファイル、POSTDEFファイルを使うのは非推奨になり、catalog.ymlを使うのが推奨になっています。

catalog.ymlの書き方については、同梱のdoc/catalog.ja.md をどうぞ。

* https://github.com/kmuto/review/blob/master/doc/catalog.ja.md

上記ファイル中でも紹介していますが、`review-catalog-converter`というコマンドを使って変換するのがおすすめです。

# :fire: シンタックスハイライトの`pygments:`が効かない

シンタックスハイライトの指定のため、config.ymlに`pygments: true`と書くことがありましたが、Pygments以外でのシンタックスハイライトを考慮して、現在は以下のように指定します。

[コード]

# :fire: inaobuilderが使えない

inao記法に変換するINAOBuilderですが、最近はMarkdownから直接InDesignに変換して使うことが多くなり、inao記法の需要が減った上にあまりメンテナンスされていなかったため、廃止されました。今後はMARKDOWNBuilderをお使いください。

# :fire: config.ymlの`appendix_format:`が効かない

個人的には`appendix_format:`を使ったことがないので詳しくないのですが……付録などの採番でローマ数字にする場合などの指定が変わりました。この問題は文書の設定の問題というよりは（言語依存の）表示の問題である、ということで、config.ymlではなくlocale.ymlの方で指定してください。

具体的な指定方法は doc/format.ja.md の「Re:VIEWカスタムフォーマット」 を参考にしてください。

# :fire: `review-epubmaker-legacy`が使えない

review-epubmakerは以前大きな変更(libepubmakerの取り込み)があったのですが、その際にもともとあった方をreview-epubmaker-legacyとして実行できるようにしていました。しかし、現在では新版のreview-epubmakerが安定して動いているため、ついに廃止されました。今後はreview-epubmakerコマンドをご利用ください。

# :fire: `review-compile --all`が使えない

`review-compile`コマンドは変換したい*.reファイルのファイル名を引数にして使うのが一般的ですが、全ファイルをまとめて変換したい場合もあります。そのために`--all`あるいは`-a`というオプションがありました。が、「変換対象のファイル名がなければ全部変換すればいいのでは…？」という意見とPull Requestがあったため、`--all`がなくてもファイル名が与えられなければまとめて変換するように変更になりました。

というわけで、`--all`・`-a`を実行していた場合は、単純に`--all`あるいは`-a`を削除して実行するようにしてください。
