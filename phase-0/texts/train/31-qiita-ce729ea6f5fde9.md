# Bracketsと.xhtmlファイルの編集

BracketsはAdobe製のオープンソースなコードエディタです。

http://brackets.io/

BracketsはHTMLファイルのlive previewができて捗るのですが、残念ながら拡張子が.xhtmlなファイルではできないようになっています。修正方法は簡単で、issuesにも上がっているのですが、どうもガチなX(HT)MLだとCDATAの扱いとかが云々…という理由で取り込まれていないようでした。

が、その辺りは気にせず変なファイルは作らない前提で.xhtmlファイルを編集したい！　という場合には、自力で修正してビルドすることになります。

# BracketsをOS Xでビルドする

Bracketsのソースはgithubにあります。本体のbracketsとビルド用のbrackets-shellに分かれています。

* https://github.com/adobe/brackets
* https://github.com/adobe/brackets-shell

ビルド方法はbrackets-shellの方のWikiの Building Brackets Shellの方に書かれています。

まずは両方のプロジェクトのソースを取得します。

[コード]

ビルドにはgit、python、Xcode4が必要です。その辺りはお好きにご用意下さい。

あとはNode.jsが必要です。私はnodebrewでインストールしました。

[コード]

brackets-shellのディレクトリに移動して、Gruntをインストールします。

[コード]

この状態で``grunt --help``を実行すると、いろいろタスクが表示されます。

ここまで来たら、``grunt build``でビルドします。

[コード]

こんなふうに表示されればビルドの完了です。
xcodebuild/Release　の下に Brackets.app ができているはずです。

# Bracketsを起動する

普通にFinderなどからBrackets.appをダブルクリックしてもいいのですが、bracketsプロジェクトからターミナルを使って起動する場合は以下になります。

[コード]

通常のbracketアプリとは異なり、起動直後はファイル選択のダイアログが表示されるので、ここでbracketsプロジェクトの下の``src/index.html``を選択します。そうすると、通常配布されているアプリを起動した時と同じ画面になります。

# .xhtmlのlive previewのためのhack

本題に戻ると、.xhtmlファイルをlive previewするにはbracketsプロジェクトの方のsrc/file/FileUtils.jsに以下のパッチをあてます。

[コード]

この状態で再度``grunt build``を実行してバイナリを作り直すと、.xhtmlファイルを開いた場合でもlive previewができるようになっているはずです。
