import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime
from github import Github

# ==========================================
# 0. 認証機能（追加）
# ==========================================
def check_password():
    """パスワード認証を行い、認証成功ならTrueを返す"""
    # セッションステートに認証状態がない場合は初期化
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    # すでに認証済みなら即座にTrueを返す
    if st.session_state.password_correct:
        return True

    # --- ログイン画面の表示 ---
    st.set_page_config(page_title="ログイン", layout="centered")
    st.title("🔒 ログイン")
    
    # パスワード入力フォーム
    password_input = st.text_input("パスワードを入力してください", type="password")
    
    if st.button("ログイン", type="primary"):
        # 設定したいパスワード（ここでは "admin" としていますが、後述の方法で安全に管理できます）
        # st.secrets を使うとより安全ですが、まずは簡易的に変数で指定します
        CORRECT_PASSWORD = st.secrets["PASSWORD"]

        if password_input == CORRECT_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()  # 画面を再読み込みしてメインアプリを表示
        else:
            st.error("パスワードが違います")
            
    return False

# ==========================================
# 1. 設定エリア
# ==========================================
APP_CONFIG = {
    "title": "My みしゅらん 🌟",
    "save_file": "gourmet_data.json",
    "genres": ["和食", "洋食", "中華", "イタリアン", "フレンチ", "スペイン", "ラーメン", "カフェ", "焼肉", "居酒屋", "スイーツ", "その他"],
    "colors": ["Black", "Gold", "Silver", "Bronze", "Normal"],
    "criteria": [
        {"id": "total", "label": "満足度　", "type": "slider", "min": 0, "max": 5},
        {"id": "taste", "label": "料理　　", "type": "slider", "min": 0, "max": 5},
        {"id": "service", "label": "サービス", "type": "slider", "min": 0, "max": 5},
        {"id": "specialty", "label": "特別感　", "type": "slider", "min": 0, "max": 5},
        {"id": "cost_performance", "label": "金額　　", "type": "slider", "min": 1, "max": 5},
        {"id": "location", "label": "場所　　", "type": "text"},
        {"id": "atmosphere", "label": "雰囲気　", "type": "selectbox", "options": ["静か", "賑やか", "個室あり", "デート向き", "入りやすい"]},
        {"id": "parking", "label": "駐車場　", "type": "selectbox", "options": ["あり","なし"]},
        {"id": "memo", "label": "メモ　　", "type": "text_area"},
    ]
}


# ==========================================
# 2. データ処理関数（GitHub版）
# ==========================================

def load_data():
    """
    読み込みはこれまで通りローカルのJSONファイルから行う
    （Streamlit Cloudはリポジトリの最新状態をcloneして起動するため）
    """
    if not os.path.exists(APP_CONFIG["save_file"]):
        return []
    with open(APP_CONFIG["save_file"], "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return []
            
    return sorted(data, key=lambda x: x.get("order", 0))

def save_data(data):
    """
    ローカルとGitHubの両方を更新してデータを保存する
    """
    # 1. データの並び替え
    data = sorted(data, key=lambda x: x.get("order", 0))
    
    # 2. JSON文字列を作成
    json_content = json.dumps(data, ensure_ascii=False, indent=4)
    
    # -------------------------------------------------
    # A. ローカルファイルへの保存（画面への即時反映用）
    # -------------------------------------------------
    try:
        with open(APP_CONFIG["save_file"], "w", encoding="utf-8") as f:
            f.write(json_content)
    except Exception as e:
        st.error(f"ローカル保存エラー: {e}")

    # -------------------------------------------------
    # B. GitHubへの保存（データの恒久化用）
    # -------------------------------------------------
    try:
        # 認証
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_user(st.secrets["GITHUB_USERNAME"]).get_repo(st.secrets["GITHUB_REPO_NAME"])
        file_path = st.secrets["DATA_FILE_PATH"]
        
        try:
            # 既存のファイルを取得（更新用）
            contents = repo.get_contents(file_path)
            repo.update_file(contents.path, "Update gourmet_data.json", json_content, contents.sha)
            st.toast("☁️ クラウド(GitHub)に保存しました！", icon="✅")
            
        except Exception:
            # ファイルがまだない場合は新規作成
            repo.create_file(file_path, "Create gourmet_data.json", json_content)
            st.toast("☁️ 新規ファイルを作成しました！", icon="✅")
            
    except Exception as e:
        st.error(f"GitHub保存エラー: {e}")
        
    # -------------------------------------------------
    # C. 通知を見せるための待機
    # -------------------------------------------------
    # これがないと、rerun()によって一瞬でメッセージが消えてしまいます
    time.sleep(2)

# ==========================================
# 削除確認ダイアログ（モーダル）
# ==========================================
@st.dialog("削除の確認")
def show_delete_dialog(item_data, current_data):
    st.write(f"本当に **「{item_data['name']}」** を削除しますか？")
    st.warning("⚠️この操作は取り消せません。")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("はい、削除します", type="primary", use_container_width=True):
            # 削除処理を実行
            new_data = [d for d in current_data if d['id'] != item_data['id']]
            save_data(new_data)
            st.rerun() # 完了後にリロード
    with col2:
        if st.button("キャンセル", use_container_width=True):
            st.rerun() # ダイアログを閉じる

# ==========================================
# 3. アプリのメイン処理
# ==========================================
def main():
    # ★追加：パスワードチェック
    # 認証が通っていない場合は、ここで処理を終了（return）させて画面を描画させない
    if not check_password():
        return

    # ★移動：set_page_config は check_password 内で呼ばれる場合と競合しないよう注意が必要ですが、
    # Streamlitの仕様上、最初に呼ばれたものが有効になります。
    # ログイン後はここで再設定されます。
    st.set_page_config(page_title=APP_CONFIG["title"], layout="wide")
    
    def local_css(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    if os.path.exists("style.css"):
        local_css("style.css")

    st.title(f"{APP_CONFIG['title']}")

    with st.expander("ランク・評価の基準について", expanded=False):
            # カードランクの説明
            st.markdown("""
            #### カードの色（ランク）
            「自分の中の特別感」で使い分けます。
            | カラー | 解説 | 
            |  --- | --- | 
            | **Black**  | **殿堂入り**：実質的なランクを問わず思い出や体験に基づく主観も含めて判定。 | 
            | **Gold**   | **至高**：感動する。自信をもって友人に勧められる。 | 
            | **Silver** | **秀逸**：非常に満足。普段使いでリピートしたい。 | 
            | **Bronze** | **優良**：安定のクオリティ。友人にお店の候補として教える。 | 
            | **Normal** | **良好**：記録用または新しく開拓中のお店。        | 
            """)
            # 区切り線を入れる
            st.divider()
            # "★"評価の目安委の説明
            st.markdown("""
            #### "★"評価の目安
            各項目の基準です。
            | 評価 | 解説 | 
            |  --- | --- | 
            | **★★★★★** | 記憶に残る強烈な印象。 | 
            | **★★★★☆** | 期待を遥かに凌駕する。 | 
            | **★★★☆☆** | 期待を大きく上回る。  | 
            | **★★☆☆☆** | 期待を上回る。 | 
            | **★☆☆☆☆** | 期待通りのクオリティ。 | 
            """)
                        # 区切り線を入れる
            st.divider()
            # "￥"評価の目安委の説明
            st.markdown("""
            #### "￥"評価の目安
            予算の基準です。
            | 評価 | 解説 | 
            |  --- | --- | 
            | <span style="font-size: 0.78em;">**￥￥￥￥￥**</span> | 20000円/人 以上 | 
            | <span style="font-size: 0.78em;">**￥￥￥￥**</span> | ～20000円/人 | 
            | <span style="font-size: 0.78em;">**￥￥￥**</span> | ～10000円/人 | 
            | <span style="font-size: 0.78em;">**￥￥**</span> | ～5000円/人 | 
            | <span style="font-size: 0.78em;">**￥**</span> | ～2000円/人 | 
            """, unsafe_allow_html=True)


    data = load_data()

    # サイドバー（省略なし）
    with st.sidebar:
        st.header("お店を登録")
        with st.form("entry_form", clear_on_submit=True):
            name = st.text_input("店名")
            card_color = st.selectbox("カードの色（ランク）", APP_CONFIG["colors"])
            date = st.date_input("訪問日", datetime.today())
            genre = st.selectbox("ジャンル", APP_CONFIG["genres"])
            url = st.text_input("URL")

            inputs = {}
            for item in APP_CONFIG["criteria"]:
                if item["type"] == "slider":
                    inputs[item["id"]] = st.slider(item["label"], item.get("min", 1), item.get("max", 5))
                elif item["type"] == "selectbox":
                    inputs[item["id"]] = st.selectbox(item["label"], item["options"])
                elif item["type"] == "text_area":
                    inputs[item["id"]] = st.text_area(item["label"])
                elif item["type"] == "text":
                    inputs[item["id"]] = st.text_input(item["label"])

            submitted = st.form_submit_button("登録")
            
            if submitted and name:
                current_max_order = max([d.get("order", 0) for d in data], default=0)
                new_entry = {
                    "id": str(datetime.now().timestamp()),
                    "name": name,
                    "date": str(date),
                    "genre": genre,
                    "url":url,
                    "color": card_color,
                    "order": current_max_order + 1,
                    **inputs
                }
                data.append(new_entry)
                save_data(data)
                st.success("登録しました！")
                st.rerun()

    with st.sidebar:
        # (既存の登録フォームの処理の後に追加)
        st.markdown("---")
        st.header("お店を削除")
        
        # 削除対象を選択するプルダウン（名前で選ぶ）
        # 選択しやすいように "名前 (訪問日)" の形式にすると親切です
        option_map = {f"{d['name']} ({d['date']})": d['id'] for d in data}
        
        selected_label = st.selectbox(
            "削除するお店を選択", 
            options=[""] + list(option_map.keys()), # 空白を先頭に
            index=0
        )
        
        if selected_label:
            target_id = option_map[selected_label]
            target_item = next((d for d in data if d['id'] == target_id), None)
            
            # ★変更：ここをクリックすると、即削除ではなくダイアログを呼び出すように修正
            if st.button("このお店を削除する", type="primary"):
                show_delete_dialog(target_item, data)

    # ---------------------------------------
    # データ管理エリア（★ここを修正）
    # ---------------------------------------
    with st.expander("データ管理（編集・復元）", expanded=False):
        if data:
            st.markdown("### データの編集")

            st.info("💡 `order` を変更して「保存」すると並び順が変わります。")
            df = pd.DataFrame(data)
            
            # 編集用設定を作成
            my_column_config = {
                "order": st.column_config.NumberColumn("順序", step=1, required=True),
                "date": st.column_config.TextColumn("訪問日", required=True),
                "color": st.column_config.SelectboxColumn("カード色", options=APP_CONFIG["colors"], required=True),
                "genre": st.column_config.SelectboxColumn("ジャンル", options=APP_CONFIG["genres"], required=True),
                "url": st.column_config.LinkColumn("お店のURL", validate="^https?://", required=True),
                "id": st.column_config.TextColumn("ID", disabled=True),
                
                # ▼▼▼ 追加：評価項目（スライダー項目）の設定 ▼▼▼
                "total": st.column_config.NumberColumn("満足度", min_value=0, max_value=5, step=1),
                "taste": st.column_config.NumberColumn("料理", min_value=0, max_value=5, step=1),
                "service": st.column_config.NumberColumn("サービス", min_value=0, max_value=5, step=1),
                "specialty": st.column_config.NumberColumn("特別感", min_value=0, max_value=5, step=1),
                "cost_performance": st.column_config.NumberColumn("金額", min_value=1, max_value=5, step=1),
                # ▲▲▲ ここまで ▲▲▲
            }

            edited_df = st.data_editor(
                df, 
                num_rows="dynamic",
                column_config=my_column_config, # 作成した設定を適用
                column_order=["order", "name", "genre", "color", "date", "url"] + [c["id"] for c in APP_CONFIG["criteria"]]
            )
            
            col_save, col_backup = st.columns([1, 1])
            with col_save:
                if st.button("変更を保存", use_container_width=True):
                    updated_data = json.loads(edited_df.to_json(orient="records"))
                    save_data(updated_data)
                    st.success("保存しました。")
                    st.rerun()
            
            # --- バックアップダウンロード機能 ---
            with col_backup:
                # JSONデータを文字列に変換
                json_string = json.dumps(data, ensure_ascii=False, indent=4)
                # ダウンロードボタン
                st.download_button(
                    label="JSON形式でバックアップ",
                    data=json_string,
                    file_name=f"gourmet_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True,
                )

            # ★追加：データ復元機能
            st.markdown("### データの復元")
            uploaded_file = st.file_uploader("バックアップファイル(.json)をアップロードして復元", type=["json"])
            if uploaded_file is not None:
                try:
                    restored_data = json.load(uploaded_file)
                    if st.button("このデータで上書きする", type="primary"):
                        save_data(restored_data)
                        st.success("データを復元しました！")
                        st.rerun()
                except Exception as e:
                    st.error("ファイルの読み込みに失敗しました。")

    # フィルターエリア（省略なし）
    st.subheader("検索・絞り込み")
    fil_col1, fil_col2, fil_col3 = st.columns([1, 1, 1])
    with fil_col1:
        search_query = st.text_input("キーワード検索", placeholder="店名、場所 など")
    with fil_col2:
        filter_colors = st.multiselect("カードの色で絞り込み", options=APP_CONFIG["colors"])
    with fil_col3:
        filter_genres = st.multiselect("ジャンルで絞り込み", options=APP_CONFIG["genres"])
    
    display_data = data 
    if filter_genres:
        display_data = [d for d in display_data if d.get("genre") in filter_genres]
    if filter_colors:
        display_data = [d for d in display_data if d.get("color") in filter_colors]
    if search_query:
        query = search_query.lower()
        display_data = [
            d for d in display_data 
            if query in d.get("name", "").lower() or 
               query in d.get("genre", "").lower() or 
               query in d.get("location", "").lower() or 
               query in d.get("memo", "").lower()
        ]

    st.markdown(f"**表示中: {len(display_data)} 件** / 全 {len(data)} 件")
    st.divider()

            # メイン表示
    if not display_data:
        if not data:
            st.info("👈 左のサイドバーから、最初のお店を登録してみましょう！")
        else:
            st.warning("条件に一致するお店が見てかりませんでした。")

    else:
        for entry in display_data:
            color_class = f"card-{entry.get('color', 'Black')}"
            safe_id = f"card_{str(entry['id']).replace('.', '').replace('_', '')}"
            
            # --- 修正ポイント：星評価 or ￥評価の生成 ---
            front_stars = ""
            for item in APP_CONFIG["criteria"]:
                if item["type"] == "slider":
                    val = entry.get(item["id"], 1)
                    num_val = int(val) if str(val).isdigit() else 1
                    
                    # コスパ（cost_performance）の場合は ￥ を使用
                    if item["id"] == "cost_performance":
                        mark = "￥" * num_val
                        # 5つ分に満たない場合は、視認性のために薄い色や空白を入れると綺麗です
                        display_text = f"<span class='yen-rating'>{mark}</span>"
                    else:
                        # それ以外は ★ を使用
                        stars = "★" * num_val + "☆" * (5 - num_val)
                        display_text = f"<span class='star-rating'>{stars}</span>"
                    
                    front_stars += f"<div class='rating-item'><strong>{item['label']}：</strong>{display_text}</div>"

            # 裏面の詳細（HTMLタグをクラス化）
            back_info = ""
            for item in APP_CONFIG["criteria"]:
                if item["type"] != "slider":
                    val = entry.get(item["id"], "-")
                    if item["id"] == "memo":
                        back_info += f"<div class='memo-area'>{val}</div>"
                    else:
                        back_info += f"<div class='detail-area'><strong>{item['label']}：</strong> {val}</div>"

            # HTML構造
            st.markdown(f"""
            <div class="flip-card">
                <input type="checkbox" id="{safe_id}" class="flip-checkbox">
                <label for="{safe_id}" class="flip-card-inner">
                    <div class="flip-card-front card {color_class}">
                        <div class="number-tag">No.{entry.get('order', '-')}</div>
                        <h3>{entry['name']}</h3>
                        <div class="card-subtitle">{entry['genre']}</div>
                        <div class="card-subtitle">訪問日：{entry['date']}</div>
                        <a href="{entry['url']}" target="_blank" class="url-button">Google Map</a>
                        <div class="rating-item-box">{front_stars}</div>
                    </div>
                    <div class="flip-card-back card {color_class}">
                        <h3>{entry['name']}</h3>
                        {back_info}
                    </div>
                </label>
            </div>
            """, unsafe_allow_html=True)
            
if __name__ == "__main__":
    main()