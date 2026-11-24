#!/bin/bash
# SPDX-FileCopyrightText: 2026 Takumi Yamawaki
# SPDX-License-Identifier: BSD-3-Clause

ng () {
    echo "NG at Line $1"
    res=1
}
res=0

### NORMAL INPUT ###
out=$(seq 5 | ./plus)
[ "$?" = 0 ]      || ng "$LINENO"
[ "${out}" = 15 ] || ng "$LINENO"

### STRANGE INPUT ###
out=$(echo あ | ./plus)           #計算できない値を入力してみる
[ "$?" = 1 ]      || ng "$LINENO" #終了ステータスが1なのを確認
[ "${out}" = "" ] || ng "$LINENO" #上の行と入れ替えるとダメ（なぜ？）

out=$(echo | ./plus)              #なにも入力しない
[ "$?" = 1 ]      || ng "$LINENO" #これも異常終了する
[ "${out}" = "" ] || ng "$LINENO"


### LIPO: NORMAL INPUT ###
out=$(echo 11.1 | ./lipo)
[ "$?" = 0 ] || ng "$LINENO"
[ "${out}" = "11.10 V → 3セル（1セル 3.70 V）残量 約30%" ] || ng "$LINENO"

out=$(printf "11.1\n7.4\n" | ./lipo | tail -1)
[ "${out}" = "-- まとめ: 2件 / 1セル最低 3.70 V / 平均残量 約30% / 過放電 0件" ] || ng "$LINENO"

out=$(echo 3.2 | ./lipo)
[ "${out}" = "3.20 V → 1セル（1セル 3.20 V）残量 約0% / 過放電のおそれ（直ちに充電してください）" ] || ng "$LINENO"

### LIPO: STRANGE INPUT ###
out=$(echo あ | ./lipo)
[ "$?" = 1 ]      || ng "$LINENO"
[ "${out}" = "" ] || ng "$LINENO"

[ "${res}" = 0 ] && echo OK
exit $res
