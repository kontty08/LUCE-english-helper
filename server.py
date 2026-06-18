#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英語学習支援ツール用 カスタムAPI・HTTPサーバー
静的ファイルを配信しつつ、複数YouTube動画の管理（リスト・取得・削除・インポート・タイトル更新）APIを提供します。
"""

import http.server
import socketserver
import urllib.parse
import json
import os
import subprocess
from pathlib import Path
import sys

PORT = 8000
BIND = "127.0.0.1"

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed_path.query)
        script_dir = Path(__file__).resolve().parent
        trans_dir = script_dir / "transcripts"
        
        if parsed_path.path == '/api/load_video':
            url_or_id = query.get('url_or_id', [None])[0]
            if not url_or_id:
                self.send_error_response(400, "Missing parameter 'url_or_id'")
                return
                
            print(f"[API] Video import request received for: {url_or_id}")
            
            try:
                # load_video.py を外部プロセスとして実行
                cmd = ["python3", "load_video.py", url_or_id]
                result = subprocess.run(cmd, cwd=script_dir, capture_output=True, text=True)
                
                if result.returncode != 0:
                    error_msg = result.stderr.strip() or result.stdout.strip() or "Failed to run load_video.py"
                    print(f"[API] Error running load_video.py: {error_msg}")
                    self.send_error_response(500, error_msg)
                    return
                
                # 生成された transcripts.js からデータを読み込む
                js_path = script_dir / "transcripts.js"
                if not js_path.exists():
                    self.send_error_response(500, "transcripts.js was not generated")
                    return
                    
                with open(js_path, "r", encoding="utf-8") as f:
                    js_content = f.read()
                    
                json_str = js_content.replace("const transcriptsData = ", "", 1).strip()
                if json_str.endswith(";"):
                    json_str = json_str[:-1]
                    
                data = json.loads(json_str)
                video_id = data.get("videoId")
                
                # 個別JSONファイルとしても保存する
                if video_id:
                    data["title"] = f"Video ({video_id})" # 初期仮タイトル
                    target_json = trans_dir / f"{video_id}.json"
                    with open(target_json, "w", encoding="utf-8") as out:
                        json.dump(data, out, ensure_ascii=False, indent=2)
                    print(f"[API] Saved copy to transcripts/{video_id}.json")
                
                self.send_json_response(data)
                
            except Exception as e:
                print(f"[API] Internal error during load_video: {e}")
                self.send_error_response(500, str(e))
                
        elif parsed_path.path == '/api/list_videos':
            videos = []
            if trans_dir.exists():
                for file_name in os.listdir(trans_dir):
                    if file_name.endswith(".json"):
                        file_path = trans_dir / file_name
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            videos.append({
                                "videoId": data.get("videoId"),
                                "title": data.get("title") or data.get("videoId")
                            })
                        except Exception as e:
                            print(f"[API] Error reading list item {file_name}: {e}")
            self.send_json_response(videos)
            
        elif parsed_path.path == '/api/get_video':
            video_id = query.get('v', [None])[0]
            if not video_id:
                self.send_error_response(400, "Missing parameter 'v'")
                return
            
            file_path = trans_dir / f"{video_id}.json"
            if not file_path.exists():
                self.send_error_response(404, f"Video {video_id} not found")
                return
                
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.send_json_response(data)
            except Exception as e:
                self.send_error_response(500, str(e))
                
        elif parsed_path.path == '/api/delete_video':
            video_id = query.get('v', [None])[0]
            if not video_id:
                self.send_error_response(400, "Missing parameter 'v'")
                return
                
            file_path = trans_dir / f"{video_id}.json"
            if not file_path.exists():
                self.send_error_response(404, f"Video {video_id} not found")
                return
                
            try:
                os.remove(file_path)
                print(f"[API] Deleted video: {video_id}")
                self.send_json_response({"success": True})
            except Exception as e:
                self.send_error_response(500, str(e))
                
        elif parsed_path.path == '/api/update_title':
            video_id = query.get('v', [None])[0]
            title = query.get('title', [None])[0]
            if not video_id or not title:
                self.send_error_response(400, "Missing parameter 'v' or 'title'")
                return
                
            file_path = trans_dir / f"{video_id}.json"
            if not file_path.exists():
                self.send_error_response(404, f"Video {video_id} not found")
                return
                
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["title"] = title
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"[API] Updated title for {video_id}: {title}")
                self.send_json_response({"success": True})
            except Exception as e:
                self.send_error_response(500, str(e))
        else:
            # 通常の静的ファイル配信
            super().do_GET()

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode('utf-8'))

def init_transcripts_dir():
    script_dir = Path(__file__).resolve().parent
    trans_dir = script_dir / "transcripts"
    trans_dir.mkdir(exist_ok=True)
    
    # マイグレーション： transcripts.js から最初の動画データを transcripts/配下へインポート
    js_path = script_dir / "transcripts.js"
    if js_path.exists():
        try:
            with open(js_path, "r", encoding="utf-8") as f:
                js_content = f.read()
            json_str = js_content.replace("const transcriptsData = ", "", 1).strip()
            if json_str.endswith(";"):
                json_str = json_str[:-1]
            data = json.loads(json_str)
            video_id = data.get("videoId")
            if video_id:
                target_json = trans_dir / f"{video_id}.json"
                if not target_json.exists():
                    data["title"] = "Ferrari Luce (Default)"
                    with open(target_json, "w", encoding="utf-8") as out:
                        json.dump(data, out, ensure_ascii=False, indent=2)
                    print(f"[Init] Migrated transcripts.js into transcripts/{video_id}.json")
        except Exception as e:
            print(f"[Init] Migration failed: {e}")

def main():
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)
    
    # transcripts フォルダと初期マイグレーションの実行
    init_transcripts_dir()
    
    handler = CustomHandler
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        with socketserver.TCPServer((BIND, PORT), handler) as httpd:
            print(f"🚀 Custom Server started at http://{BIND}:{PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()