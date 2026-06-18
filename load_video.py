#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英語学習支援ツール用 ビデオ読み込みスクリプト
指定されたYouTube動画の字幕を取得し、transcripts.json に自動更新します。

使い方:
  python3 load_video.py <YouTube_URLまたはVideoID>

例:
  python3 load_video.py "https://www.youtube.com/watch?v=K-o0r2zSgCE"
"""

import os
import re
import sys
import json
import subprocess
from pathlib import Path

# ── タイムスタンプを秒数に変換 ─────────────────────────
def time_to_seconds(t_str):
    parts = t_str.strip().split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0

# ── VTTファイルをパース ────────────────────────────────
def parse_vtt(vtt_path):
    if not os.path.exists(vtt_path):
        return []
    
    with open(vtt_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    blocks = re.split(r'\n\s*\n', content)
    subtitles = []
    
    for block in blocks:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue
        
        time_line = None
        text_lines = []
        
        for line in lines:
            if "-->" in line:
                time_line = line
            elif time_line:
                text_lines.append(line)
                
        if time_line and text_lines:
            match = re.search(r'([\d:.]+)\s*-->\s*([\d:.]+)', time_line)
            if match:
                start_sec = time_to_seconds(match.group(1))
                end_sec = time_to_seconds(match.group(2))
                
                text = " ".join(text_lines)
                text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"').replace("&apos;", "'")
                text = re.sub(r'\s+', ' ', text).strip()
                
                if text:
                    subtitles.append({
                        "start": start_sec,
                        "end": end_sec,
                        "text": text
                    })
                    
    return subtitles

# ── 字幕のセンテンスベース再構成 ──────────────────────
def reconstruct_into_sentences(raw_subtitles, max_words=20, max_duration=8.0):
    """
    生の字幕セグメントを、文（センテンス）ごとに再構成します。
    時間の割り当ては単語数ベースで線形補間します。
    """
    # 省略語のリスト（これらの後ろのピリオドは文末とみなさない）
    ABBREVIATIONS = {
        "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "vs", "co", "corp", "inc", "ltd",
        "st", "ave", "rd", "etc", "approx", "eg", "ie", "al", "vol", "ed", "pp", "sec",
        "min", "hr", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec"
    }

    # 1. すべての単語をフラットなリストに分解し、時間情報を付与
    all_words = []
    for cue in raw_subtitles:
        text = cue["text"].strip()
        if not text:
            continue
        words = text.split()
        if not words:
            continue
        
        duration = cue["end"] - cue["start"]
        word_dur = duration / len(words)
        
        for i, w in enumerate(words):
            all_words.append({
                "text": w,
                "start": cue["start"] + i * word_dur,
                "end": cue["start"] + (i + 1) * word_dur
            })
            
    if not all_words:
        return []

    # 2. 単語リストを走査して、センテンスごとに結合
    sentences = []
    current_words = []
    
    def is_sentence_end(word_info):
        word = word_info["text"]
        # 末尾が . ? ! で終わるか判定（後ろにクォーテーション等があっても考慮）
        if not re.search(r'[.?!]["\']?$', word):
            return False
            
        # 省略語チェック（ピリオドや記号を除去した英単語が省略語リストに含まれるか）
        cleaned = re.sub(r'[^\w]', '', word).lower()
        if cleaned in ABBREVIATIONS:
            return False
            
        return True

    for w_info in all_words:
        current_words.append(w_info)
        
        # 文末判定、または制限値（最大単語数や最大時間）を超えた場合
        should_split = False
        if is_sentence_end(w_info):
            should_split = True
        elif len(current_words) >= max_words:
            should_split = True
        elif (w_info["end"] - current_words[0]["start"]) >= max_duration:
            should_split = True
            
        if should_split:
            text = " ".join([x["text"] for x in current_words])
            sentences.append({
                "start": round(current_words[0]["start"], 2),
                "end": round(current_words[-1]["end"], 2),
                "text": text
            })
            current_words = []
            
    # 残った単語があれば追加
    if current_words:
        text = " ".join([x["text"] for x in current_words])
        sentences.append({
            "start": round(current_words[0]["start"], 2),
            "end": round(current_words[-1]["end"], 2),
            "text": text
        })
        
    return sentences

# ── ビデオIDの抽出 ───────────────────────────────────
def extract_video_id(url_or_id):
    url_or_id = url_or_id.strip()
    if len(url_or_id) == 11 and re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
        
    # Extract from watch?v=... or youtu.be/...
    match = re.search(r'(?:v=|\/v\/|embed\/|youtu\.be\/|\/shorts\/|^)([a-zA-Z0-9_-]{11})', url_or_id)
    if match:
        return match.group(1)
    return None

def main():
    if len(sys.argv) < 2:
        print("❌ エラー: YouTubeのURLまたはビデオIDを指定してください。")
        print("使用例: python3 load_video.py https://www.youtube.com/watch?v=K-o0r2zSgCE")
        sys.exit(1)
        
    input_val = sys.argv[1]
    video_id = extract_video_id(input_val)
    
    if not video_id:
        print(f"❌ エラー: 有効なYouTubeビデオIDを抽出できませんでした: {input_val}")
        sys.exit(1)
        
    print(f"📺 対象ビデオID: {video_id}")
    print("⏳ 字幕を取得しています (yt-dlp)...")
    
    temp_prefix = f"temp_{video_id}"
    vtt_file = f"{temp_prefix}.en.vtt"
    
    # Clean up previous temp files if they exist
    if os.path.exists(vtt_file):
        os.remove(vtt_file)
        
    # Run yt-dlp to fetch subtitles (prefer manual english subtitles, fallback to auto)
    # --skip-download skips video downloading.
    try:
        # Step 1: try manual subtitles first
        print("🔍 手動英語字幕を探しています...")
        subprocess.run([
            "yt-dlp",
            "--write-subs",
            "--sub-lang", "en",
            "--skip-download",
            "-o", temp_prefix,
            f"https://www.youtube.com/watch?v={video_id}"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Step 2: if manual not found, try auto-generated subtitles
        if not os.path.exists(vtt_file):
            print("🔍 手動字幕が見つからないため、自動生成字幕（英語）を取得しています...")
            subprocess.run([
                "yt-dlp",
                "--write-auto-subs",
                "--sub-lang", "en",
                "--skip-download",
                "-o", temp_prefix,
                f"https://www.youtube.com/watch?v={video_id}"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        if not os.path.exists(vtt_file):
            print("❌ エラー: 英語の字幕（手動・自動）を取得できませんでした。")
            sys.exit(1)
            
        # Parse VTT
        print("⚙️  字幕データをパースしています...")
        raw_subtitles = parse_vtt(vtt_file)
        
        if not raw_subtitles:
            print("❌ エラー: 字幕のパース結果が空です。")
            if os.path.exists(vtt_file):
                os.remove(vtt_file)
            sys.exit(1)
            
        # Reconstruct into sentences
        print("📝 字幕をセンテンスベースに再構成しています...")
        subtitles = reconstruct_into_sentences(raw_subtitles)
        
        # Structure new JSON
        data_to_save = {
            "videoId": video_id,
            "subtitles": subtitles
        }
        
        # Save to transcripts.js
        output_path = Path(__file__).resolve().parent / "transcripts.js"
        with open(output_path, "w", encoding="utf-8") as out_f:
            out_f.write("const transcriptsData = ")
            json.dump(data_to_save, out_f, ensure_ascii=False, indent=2)
            out_f.write(";\n")
            
        print(f"🎉 成功: {len(subtitles)} 件の字幕を {output_path.name} に保存しました。")
        print("💡 ブラウザで index.html をリロード（またはダブルクリック）して学習を開始してください！")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
    finally:
        # Cleanup
        if os.path.exists(vtt_file):
            os.remove(vtt_file)

if __name__ == "__main__":
    main()
