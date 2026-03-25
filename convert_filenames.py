#!/usr/bin/env python3
"""
ボイスファイル名変換スクリプト
AA_B_C.wav  →  <Base64エンコード>.dat  （難読化）
<Base64エンコード>.dat  →  AA_B_C.wav  （復元）

使い方:
  python convert_filenames.py encode  <入力フォルダ> <出力フォルダ>
  python convert_filenames.py decode  <入力フォルダ> <出力フォルダ>
  python convert_filenames.py mapping <入力フォルダ>   # マッピング表を表示するだけ
"""

import os
import sys
import shutil
import base64
import json


# ---------- コア変換関数 ----------

def encode_filename(original_stem: str) -> str:
    """
    元のファイル名（拡張子なし）を Base64 エンコードして返す。
    URL-safe Base64 を使用し、末尾の '=' パディングは除去する。
    ファイルシステムで問題になる文字（/ など）が入らないよう urlsafe を採用。
    """
    encoded = base64.urlsafe_b64encode(original_stem.encode("utf-8"))
    return encoded.decode("ascii").rstrip("=")


def decode_filename(encoded_stem: str) -> str:
    """
    Base64 エンコードされたファイル名（拡張子なし）を元に戻す。
    除去したパディングを補填してからデコードする。
    """
    padding = 4 - len(encoded_stem) % 4
    if padding != 4:
        encoded_stem += "=" * padding
    return base64.urlsafe_b64decode(encoded_stem.encode("ascii")).decode("utf-8")


# ---------- ファイル操作 ----------

def encode_files(src_dir: str, dst_dir: str) -> dict:
    """
    src_dir 内の *.wav を Base64 名の *.dat として dst_dir にコピーする。
    戻り値: {エンコード後ファイル名: 元ファイル名} のマッピング辞書
    """
    os.makedirs(dst_dir, exist_ok=True)
    mapping = {}  # encoded_name -> original_name

    for fname in sorted(os.listdir(src_dir)):
        if not fname.lower().endswith(".wav"):
            continue
        stem = os.path.splitext(fname)[0]
        encoded_stem = encode_filename(stem)
        new_name = encoded_stem + ".dat"

        src_path = os.path.join(src_dir, fname)
        dst_path = os.path.join(dst_dir, new_name)
        shutil.copy2(src_path, dst_path)

        mapping[new_name] = fname
        print(f"  {fname}  →  {new_name}")

    # マッピング JSON を出力フォルダに保存（復元に使える）
    mapping_path = os.path.join(dst_dir, "mapping.json")
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"\nマッピング表を保存しました: {mapping_path}")
    return mapping


def decode_files(src_dir: str, dst_dir: str) -> None:
    """
    src_dir 内の *.dat を元の *.wav 名に戻して dst_dir にコピーする。
    mapping.json があればそちらを優先し、なければ Base64 デコードで復元する。
    """
    os.makedirs(dst_dir, exist_ok=True)

    # mapping.json があれば読み込む
    mapping_path = os.path.join(src_dir, "mapping.json")
    mapping = {}
    if os.path.exists(mapping_path):
        with open(mapping_path, encoding="utf-8") as f:
            mapping = json.load(f)
        print("mapping.json を使って復元します。")
    else:
        print("mapping.json が見つかりません。Base64 デコードで復元します。")

    for fname in sorted(os.listdir(src_dir)):
        if not fname.lower().endswith(".dat"):
            continue

        if fname in mapping:
            original_name = mapping[fname]
        else:
            # mapping なし → Base64 デコードで復元
            stem = os.path.splitext(fname)[0]
            try:
                original_stem = decode_filename(stem)
                original_name = original_stem + ".wav"
            except Exception as e:
                print(f"  [スキップ] {fname}: デコード失敗 ({e})")
                continue

        src_path = os.path.join(src_dir, fname)
        dst_path = os.path.join(dst_dir, original_name)
        shutil.copy2(src_path, dst_path)
        print(f"  {fname}  →  {original_name}")


def show_mapping(src_dir: str) -> None:
    """src_dir 内の *.wav のエンコード結果を表示するだけ（ファイルコピーなし）"""
    print(f"{'元ファイル名':<50} {'変換後ファイル名'}")
    print("-" * 80)
    for fname in sorted(os.listdir(src_dir)):
        if not fname.lower().endswith(".wav"):
            continue
        stem = os.path.splitext(fname)[0]
        encoded_stem = encode_filename(stem)
        new_name = encoded_stem + ".dat"
        print(f"{fname:<50} {new_name}")


# ---------- エントリーポイント ----------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "encode":
        if len(sys.argv) < 4:
            print("使い方: python convert_filenames.py encode <入力フォルダ> <出力フォルダ>")
            sys.exit(1)
        encode_files(sys.argv[2], sys.argv[3])

    elif command == "decode":
        if len(sys.argv) < 4:
            print("使い方: python convert_filenames.py decode <入力フォルダ> <出力フォルダ>")
            sys.exit(1)
        decode_files(sys.argv[2], sys.argv[3])

    elif command == "mapping":
        if len(sys.argv) < 3:
            print("使い方: python convert_filenames.py mapping <入力フォルダ>")
            sys.exit(1)
        show_mapping(sys.argv[2])

    else:
        print(f"不明なコマンド: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
