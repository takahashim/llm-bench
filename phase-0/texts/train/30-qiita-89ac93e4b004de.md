mbedはWebブラウザ経由で使えるIDEが用意されており、サーバサイドでビルドするとビルド結果のバイナリがサーバから降ってくる、という（公開当時としては）すごい仕組みで一躍注目を集めました。

が、mbed SDKがオープンソースとして(Apache License v2)公開された際、ビルドツールも合わせて公開されました。これにより、ローカルのコンパイラ等を使ってバイナリをビルドすることもできるようになりました。

というわけで、mbedをMac OS X上でビルドする方法です。Linux等のUnixでもほぼ同様だと思います。

# mbedのローカルビルドシステム概要

ビルド関連のツールの使い方は、mbed handbookページ内の「mbed tools」のページでざっくり書かれています。

* mbed tools (https://mbed.org/handbook/mbed-tools)
* 同日本語訳 (https://mbed.org/users/MACRUM/notebook/mbed-tools/)

## ビルドツールに必要なもの

mbedビルドツールに必要な物は以下です。

* git
* Python
    * Jinja2
* ツールチェイン（コンパイラ、IDE等）

gitとPythonはお好きなやり方でインストールしておいてください。Pythonは3系では動かなさそうなので、2.7とかを使うと良さそうです。OS X標準のものを使うのがお手軽そうです。

Jinja2はPythonのテンプレートエンジンだそうです。

* Jinja2 http://jinja.pocoo.org/docs/

テンプレートエンジンだからTemple→Jinja、というベタな発想のネーミングだそうでびっくりです。こちらはeasy_installやpipとかを使ってインストールしておいてください。

[コード]

コンパイラについては、当然のようにGNUツールチェインを使います。GCCにもいろいろあるわけですが、mbedではGNU Tools for ARM Embedded Processorsを使うのがおすすめだそうなのでこちらをインストールしておきます。

* GCC ARM Embedded in Launchpad https://launchpad.net/gcc-arm-embedded

OS Xではバイナリファイルが配布されているので、ダウンロードしてPATHを通しておきましょう。HomebrewやMacPortsを使ってもよいかもです。

ちなみにビルドするだけならmbedのプラットフォームというかハードウェアは必要ありません。とはいえビルドする際にはプラットフォームを指定する必要があるので、実際に使いたいハードウェアを調べておく必要はあります。

## ビルドツールの入手

mbedビルドツールのソースはmbed SDKの中に入っています。mbed SDKはgithubから持ってきます。

* mbed SDK https://github.com/mbedmicro/mbed

こんな感じです。

[コード]

いろいろファイルが入っていますが、ビルドに使うコマンドファイルは以下の２つです。

* workspace_tools/build.py
* workspace_tools/make.py

build.pyはmbedのライブラリのビルド用、make.pyがmbedのアプリケーションのビルド用、ということのようです。

それ以外にも、設定ファイルとして``workspace_tools/private_settings.py``を使います。標準の設定は``workspace_tools/settings.py``というファイルを実行して取得するのですが、それ以外に設定したい場合はprivate_settings.pyに記述します。

# mbedライブラリをビルドする

アプリケーションをビルドする前に、mbedライブラリを作っておきます。こちらは先述の通りbuild.pyを使います。

build.pyのオプションを知るには、``-h``をつけて実行すると表示されます。

[コード]

出力結果の１行目のように、private_settings.pyを作らないと警告が出ます。とりあえず空のファイルでも用意しておけば、この警告は出なくなります。

[コード]

気を取り直して中身を見てみましょう。``Options:``以下がオプションです。

ここで重要なのは``-m``と``-t``です。この2つはbuild.py、make.py共通のオプションで、それぞれmbedで使いたいプラットフォームのMCUというかボードと、ツールチェインを指定します。

mbed handbookの「mbed tools」で書かれているものよりもずいぶんと増えていて、ドキュメントが追いついていないようです。

-mで指定できるMCUは以下の通りです。

* STM32F3XX
* UBLOX_C027
* DISCO_F100RB
* NRF51822
* LPC11U35_401
* LPC1549
* K64F
* LPC1347
* STM32F407
* NUCLEO_L152RE
* LPC11U35_501
* NUCLEO_F302R8
* LPC2368
* LPC810
* LPC812
* KL05Z
* LPC11U68
* LPC4088
* LPC1114
* NUCLEO_F072RB
* NUCLEO_L053R8
* LPC11U24_301
* LPC4330_M4
* LPC11C24
* DISCO_F051R8
* KL46Z
* DISCO_F303VC
* NUCLEO_F103RB
* KL25Z
* NUCLEO_F030R8
* LPC1768
* K20D5M
* NUCLEO_F401RE
* LPC11U24
* DISCO_F407VG

ずいぶん増えてますね……。mbed対応ボードは現在も順調に増えていっているようで、ここに含まれていないものも今後は増えるような気がします。

``-t``で指定するビルド用のツールチェインは以下です。

* GCC_ARM (ARM版GCC)
* GCC_CS (CodeSourcery版GCC)
* GCC_CR (CodeRed版GCC)
* GCC_CW_NEWLIB (CodeWarrior+GCC+newlib??)
* GCC_CW_EWL (CodeWarrior+GCC+Embedded Warrior Library??)
* uARM (ARMCC + micro Cライブラリ)
* ARM (ARMCC + 標準Cライブラリ)
* IAR (IARツールチェイン)

GCC_CW_*はよく分からないのですがfreescaleっぽい気がします。本記事では一番上のGCC_ARMを使います。コマンドで言うと arm-none-eabi-gcc とかです。

MCUはNUCLEOのF401RE、ツールチェインはGCC(GNU Tools for ARM Embedded Processors)の場合、ビルドは以下のようになります。

[コード]

こうすると、``build/mbed/``というディレクトリができて、その下の階層にヘッダファイル(.h)やオブジェクトファイル(.o)ができます。これでmbedアプリケーションを作る準備ができました。

# mbedアプリケーションをビルドする

ここまで来てようやくアプリケーションのビルドです。

こちらもオプションを調べるところから始めてみます。``-h``オプションつきで実行します。

[コード]

いろいろオプションがついていますが、テスト用プログラムを実行するには``-p``オプションか``-n``オプションをつけるだけでビルドできます。``-p``オプションはテストプログラムの番号を、``-n``オプションはプログラム名を一緒に渡すことで、どのテストプログラムをビルドするかを指定します。

指定できるテストプログラムのリストを表示するには、make.pyに``-L``オプションをつけて実行します。

[コード]

こんな感じで、100個以上だらだらっと表示されます。

とりあえずは最初の0番、MBED_A1をビルドしてみましょう。``-p 0``または``-n MBED_A1``をつけてmake.pyを実行します。

[コード]

こんな感じでビルドされ、アプリケーションのバイナリファイルbasic.binが上記ディレクトリに作られます。

バイナリファイルの生成ファイルは``-d``オプションで指定できます。~/mbed/binary/に保存するには以下のようにします。

[コード]

# 自作アプリケーションをビルドする

あらかじめ用意されているテスト用アプリケーションのビルドはこれまで説明してきた通りでいいのですが、テストとして用意されている以外の、普通に作成したソースをビルドできなければ困ります。この場合は、``-p``や``-n``の代わりに``--source``オプションと``--build``オプションを使います。``--source``オプションはソースディレクトリの指定に、``--build``オプションはビルド用ディレクトリの指定に使います（``--source``か``-p``か``-n``か、このうち最低一つは必須で、どのオプションも指定せずに実行しようとするとエラーになります）。

例えば、ソースディレクトリは~/mbed/src、ビルドディレクトリは~/med/buildにするのであれば、以下のように実行します。

[コード]

これでビルドしたバイナリがmbedハードウェアに転送されます。
