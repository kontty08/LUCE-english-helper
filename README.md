# LUCE — English Study Companion

LUCE is a lightweight, interactive web-based English learning application. It allows you to study English with YouTube videos, review synced interactive transcripts, look up words on-the-fly, and practice your speaking skills with automated pronunciation checks powered by Google's Gemini API.

---

## Key Features

1. **Interactive Subtitle Scrolling & Dictionary**:
   - Subtitles scroll smoothly in sync with the video playback.
   - Clicking any word immediately fetches its definition from an English-English dictionary.
2. **Speaking Practice & Pronunciation Checker**:
   - Record your speech via microphone.
   - The app transcribes it using Google's Gemini API and compares it with the target subtitle, highlighting correct and incorrect words.
3. **Multiple Gemini API Keys Rotation**:
   - Support for registering multiple Gemini API keys in the settings modal.
   - The app automatically rotates API keys on rate-limits (HTTP 429 / Resource Exhausted) to ensure uninterrupted learning.
4. **Interactive Subtitle timing & Text Editor**:
   - Fine-tune subtitle start/end times in 0.1-second increments.
   - Directly edit the subtitle texts.
   - Adjustments automatically cascade and align adjacent subtitle timings to avoid gaps.
5. **Visual "Word Block Editor"**:
   - Shift words between adjacent subtitle cards visually. Move selected word chips to the previous/next card with a single click.
6. **Multiple Video Library Management**:
   - Import any YouTube video by URL or Video ID.
   - Switch between videos via a header dropdown.
   - Automatically synchronizes YouTube video titles locally.
   - Easily delete videos (safely cleans up local custom subtitle edits).

---

## Tech Stack

* **Frontend**: Vanilla HTML5, CSS3, JavaScript (Inter & Outfit Google Fonts, Lucide Icons, YouTube Player Iframe API)
* **Backend**: Lightweight Python custom HTTP & API Server (`server.py`)
* **Utilities**: `yt-dlp` for subtitle retrieval and title synchronization

---

## Prerequisites

To run this tool locally, make sure you have:
1. **Python 3.x** installed.
2. **yt-dlp** command-line utility installed and available in your shell `PATH`:
   ```bash
   pip install yt-dlp
   # Or via Homebrew on macOS:
   brew install yt-dlp
   ```
3. A **Gemini API Key** (Get a free API key from [Google AI Studio](https://aistudio.google.com/)).

---

## Getting Started

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/<your-username>/english-helper.git
   cd english-helper
   ```

2. **Start the API Server**:
   ```bash
   python3 server.py
   ```
   *The server starts up and migrates default data into the `transcripts/` directory.*

3. **Open the Application**:
   - Open your web browser and navigate to: **`http://127.0.0.1:8000`**

4. **Configure API Keys**:
   - Click **Gemini 設定** (Gemini Settings) in the top-right corner.
   - Enter your Gemini API key (one per line if registering multiple keys for rotation) and save.

5. **Start Learning**:
   - Select a video from the library dropdown, or import a new one by clicking **動画の取り込み** (Import Video).

---

## License

This project is licensed under the [MIT License](LICENSE).

---

---

# LUCE — 英語学習アシスタント (日本語)

LUCEは、YouTube動画を使ってリスニング、単語検索、スピーキング練習ができるWebベースの英語学習支援ツールです。マイクで発音した音声をGoogleのGemini APIで文字起こしし、元の字幕との差分を自動比較するスピーキング評価機能を備えています。

## 主な機能
1. **連動スクロール字幕 ＆ インスタント辞書**:
   - 動画の再生時間と同期して字幕が自動スクロールし、ハイライト表示されます。
   - 単語をクリックするだけで、即座に英英辞書のポップアップが開きます。
2. **発音チェック ＆ スピーキング評価**:
   - 字幕を選択してマイクで音読すると、Gemini APIを用いて文字起こしされ、元の英語字幕との一致状況（正しい単語/正しくない単語）を色分けで判定します。
3. **複数APIキーの自動ローテーション**:
   - 設定画面から複数のGemini APIキーを登録可能です。キーがアクセス制限（429エラー）に達した場合、自動的に次のキーへと切り替えて処理を継続します。
4. **字幕タイミング ＆ テキスト調整**:
   - 各字幕セグメントの開始・終了時間を 0.1秒単位で微調整できます。
   - 変更した時間は前後の字幕と自動的に連動して調整されるため、字幕の隙間や重複が発生しません。
5. **単語ブロックエディタ**:
   - 字幕の編集画面で、テキストの各単語が「チップ」として視覚化されます。選択した単語チップをワンクリックで前後の字幕セグメントに移動させることができます。
6. **複数動画の管理（ライブラリ機能）**:
   - YouTubeのURLを入力するだけで、瞬時に英語字幕をダウンロードして新規インポートできます。
   - インポートした動画はヘッダーのドロップダウンでいつでも切り替えや、削除（ローカル編集データのクリーンアップ含む）が可能です。

## 動作要件
* Python 3.x
* `yt-dlp` (YouTube字幕データ・タイトル取得用)
  ```bash
  pip install yt-dlp
  # または macOS (Homebrew):
  brew install yt-dlp
  ```
* Google Gemini APIキー (無料枠で取得可能です)

## セットアップ手順
1. **リポジトリのクローン**:
   ```bash
   git clone https://github.com/<your-username>/english-helper.git
   cd english-helper
   ```
2. **サーバーの起動**:
   ```bash
   python3 server.py
   ```
3. **ブラウザで開く**:
   - `http://127.0.0.1:8000` にアクセスします。
4. **APIキーの設定**:
   - 右上の「Gemini設定」から取得したAPIキーを入力して保存し、学習を開始してください。
