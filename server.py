#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英語学習支援ツール用 カスタムAPI・HTTPサーバー
静的ファイルを配信しつつ、YouTube動画の取り込み用APIを提供します。
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
        if parsed_path.path == '/api/load_video':
            # クエリパラメータから動画のURLまたはIDを取得
            query = urllib.parse.parse_qs(parsed_path.query)
            url_or_id = query.get('url_or_id', [None])[0]
            
            if not url_or_id:
                self.send_error_response(400, "Missing parameter 'url_or_id'")
                return
                
            print(f"[API] Video import request received for: {url_or_id}")
            
            try:
                # load_video.py を外部プロセスとして実行
                cmd = ["python3", "load_video.py", url_or_id]
                script_dir = Path(__file__).resolve().parent
                
                # サブプロセスの実行
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
                    
                # 'const transcriptsData = ' と ';\n' を剥がして純粋なJSONオブジェクトにする
                json_str = js_content.replace("const transcriptsData = ", "", 1).strip()
                if json_str.endswith(";"):
                    json_str = json_str[:-1]
                    
                data = json.loads(json_str)
                print(f"[API] Successfully imported video: {data.get('videoId')}, {len(data.get('subtitles', []))} subtitles.")
                
                self.send_json_response(data)
                
            except Exception as e:
                print(f"[API] Internal error: {e}")
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

def main():
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)
    
    handler = CustomHandler
    
    # ポートの再利用を許可
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        with socketserver.TCPServer((BIND, PORT), handler) as httpd:
            print(f"🚀 Custom Server started at http://{BIND}:{PORT}")
            print(f"API Endpoint: http://{BIND}:{PORT}/api/load_video?url_or_id=<YouTube_URL>")
            httpd.serve_forever()
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()