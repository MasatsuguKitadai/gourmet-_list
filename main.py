import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# ==========================================
# 1. 設定エリア
# ==========================================
APP_CONFIG = {
    "title": "こだわリスト：グルメ",
    "save_file": "gourmet_data.json",
    "genres": ["和食", "洋食", "中華", "イタリアン", "フレンチ", "スペイン", "ラーメン", "カフェ", "焼肉", "居酒屋", "スイーツ", "その他"],
    "colors": ["Black", "Gold", "Silver", "Bronze", "Normal"],
    "criteria": [
        {"id": "total", "label": "満足度　", "type": "slider", "min": 1, "max": 5},
        {"id": "taste", "label": "料理　　", "type": "slider", "min": 1, "max": 5},
        {"id": "service", "label": "サービス", "type": "slider", "min": 1, "max": 5},
        {"id": "cost_performance", "label": "コスパ　", "type": "slider", "min": 1, "max": 5},
        {"id": "location", "label": "場所　　", "type": "text"},
        {"id": "atmosphere", "label": "雰囲気　", "type": "selectbox", "options": ["静か", "賑やか", "個室あり", "デート向き", "入りやすい"]},
        {"id": "parking", "label": "駐車場　", "type": "selectbox", "options": ["あり","なし"]},
        {"id": "memo", "label": "メモ　　", "type": "text_area"},
    ]
}

# ==========================================
# 2. データ処理関数
# ==========================================
def load_data():
    if not os.path.exists(APP_CONFIG["save_file"]):
        return []
    with open(APP_CONFIG["save_file"], "r", encoding="utf-8") as f:
        data = json.load(f)
        
    needs_save = False
    for i, item in enumerate(data):
        if "order" not in item:
            item["order"] = i + 1
            needs_save = True
            
    if needs_save:
        save_data(data)
        
    return sorted(data, key=lambda x: x.get("order", 0))

def save_data(data):
    data = sorted(data, key=lambda x: x.get("order", 0))
    with open(APP_CONFIG["save_file"], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ==========================================
# 3. アプリのメイン処理
# ==========================================
def main():
    st.set_page_config(page_title=APP_CONFIG["title"], layout="wide")
    
    def local_css(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    if os.path.exists("style.css"):
        local_css("style.css")

    st.title(f"{APP_CONFIG['title']}")

    data = load_data()

    # 削除確認エリア（省略なし）
    query_params = st.query_params
    if "confirm_delete" in query_params:
        target_id = query_params["confirm_delete"]
        target_entry = next((item for item in data if item["id"] == target_id), None)
        
        if target_entry:
            with st.container():
                st.warning(f"⚠️ **削除確認**： 本当に 「{target_entry['name']}」 のカードを削除しますか？")
                col1, col2, _ = st.columns([2, 2, 5]) 
                with col1:
                    if st.button("削除する", type="primary", use_container_width=True):
                        new_data = [d for d in data if d['id'] != target_id]
                        save_data(new_data)
                        st.success("削除しました")
                        st.query_params.clear()
                        st.rerun()
                with col2:
                    if st.button("キャンセル", use_container_width=True):
                        st.query_params.clear()
                        st.rerun()
            st.divider()

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

    # ---------------------------------------
    # データ管理エリア（★ここを修正）
    # ---------------------------------------
    with st.expander("データ管理（編集・並べ替え）", expanded=False):
        if data:
            st.info("💡 `order` を変更して「保存」すると並び順が変わります。")
            df = pd.DataFrame(data)
            edited_df = st.data_editor(
                df, 
                num_rows="dynamic",
                column_config={
                    "order": st.column_config.NumberColumn("順序", step=1, required=True),
                    "date": st.column_config.TextColumn("訪問日", required=True),
                    "color": st.column_config.SelectboxColumn("カード色", options=APP_CONFIG["colors"], required=True),
                    "genre": st.column_config.SelectboxColumn("ジャンル", options=APP_CONFIG["genres"], required=True),
                    "url": st.column_config.LinkColumn("お店のURL", validate="^https?://", required=True),
                    "id": st.column_config.TextColumn("ID", disabled=True)
                },
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

    # メイン表示（省略なし）
    if not display_data:
        if not data:
            st.info("👈 左のサイドバーから、最初のお店を登録してみましょう！")
        else:
            st.warning("条件に一致するお店が見つかりませんでした。")

    else:
        for entry in display_data:
            color_class = f"card-{entry.get('color', 'Black')}"
            safe_id = f"card_{str(entry['id']).replace('.', '').replace('_', '')}"
            
            # 表面の星評価（HTMLタグをクラス化）
            front_stars = ""
            for item in APP_CONFIG["criteria"]:
                if item["type"] == "slider":
                    val = entry.get(item["id"], 1)
                    num_val = int(val) if str(val).isdigit() else 1
                    stars = "★" * num_val + "☆" * (5 - num_val)
                    front_stars += f"<div class='rating-item'><strong>{item['label']}：</strong><span class='star-rating'>{stars}</span></div>"
            
            # 裏面の詳細（HTMLタグをクラス化）
            back_info = ""
            for item in APP_CONFIG["criteria"]:
                if item["type"] != "slider":
                    val = entry.get(item["id"], "-")
                    if item["id"] == "memo":
                        back_info += f"<div class='memo-area'>{val}</div>"
                    else:
                        back_info += f"<div class='detail-area'><strong>{item['label']}：</strong> {val}</div>"

            # HTML構造（デザインはすべてクラス経由で適用）
            st.markdown(f"""
            <div class="flip-card">
                <input type="checkbox" id="{safe_id}" class="flip-checkbox">
                <label for="{safe_id}" class="flip-card-inner">
                    <div class="flip-card-front card {color_class}">
                        <a href="?confirm_delete={entry['id']}" target="_self" class="delete-btn">✕</a>
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