import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# ==========================================
# 1. 設定エリア
# ==========================================
APP_CONFIG = {
    "title": "グルメ図鑑",
    "save_file": "gourmet_data.json",
    "genres": ["和食", "洋食", "中華", "イタリアン", "フレンチ", "スペイン", "ラーメン", "カフェ", "焼肉", "居酒屋", "その他"],
    "colors": ["Black", "Gold", "Silver", "Bronze", "Normal"],
    "criteria": [
        {"id": "total", "label": "満足度", "type": "slider", "min": 1, "max": 5},
        {"id": "taste", "label": "料理　", "type": "slider", "min": 1, "max": 5},
        {"id": "cost_performance", "label": "コスパ", "type": "slider", "min": 1, "max": 5},
        {"id": "location", "label": "場所　", "type": "text"},
        {"id": "atmosphere", "label": "雰囲気", "type": "selectbox", "options": ["静か", "賑やか", "個室あり", "デート向き", "入りやすい"]},
        {"id": "parking", "label": "駐車場", "type": "selectbox", "options": ["あり","なし"]},
        {"id": "memo", "label": "メモ　", "type": "text_area"},
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
        
    # データに 'order' キーがない場合、自動的に付番する
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
    
    # CSS読み込み
    def local_css(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    if os.path.exists("style.css"):
        local_css("style.css")

    st.title(f"{APP_CONFIG['title']}")

    data = load_data()

    # ---------------------------------------
    # 削除確認・実行エリア
    # ---------------------------------------
    query_params = st.query_params
    if "confirm_delete" in query_params:
        target_id = query_params["confirm_delete"]
        target_entry = next((item for item in data if item["id"] == target_id), None)
        
        if target_entry:
            with st.container():
                st.warning(f"⚠️ **削除確認**： 本当に 「{target_entry['name']}」 のカードを削除しますか？")
                col1, col2, col3 = st.columns([2, 2, 5]) 
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

    # ---------------------------------------
    # サイドバー：新規登録フォーム
    # ---------------------------------------
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
                    inputs[item["id"]] = st.text_input(item["label"], placeholder=item.get("placeholder", ""))

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
    # データ管理エリア（並べ替え機能付き）
    # ---------------------------------------
    with st.expander("データ一覧・編集・並べ替え", expanded=False):
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
            
            if st.button("変更を保存"):
                updated_data = json.loads(edited_df.to_json(orient="records"))
                save_data(updated_data)
                st.success("保存しました。")
                st.rerun()

    # ---------------------------------------
    # フィルター（絞り込み）エリア
    # ---------------------------------------
    st.subheader("検索・絞り込み")
    
    fil_col1, fil_col2, fil_col3 = st.columns([1, 1, 1])
    
    with fil_col1:
        search_query = st.text_input("店名で検索", placeholder="店名を入力...")

    with fil_col2:
        filter_genres = st.multiselect("ジャンルで絞り込み", options=APP_CONFIG["genres"])
    
    with fil_col3:
        filter_colors = st.multiselect("カードの色で絞り込み", options=APP_CONFIG["colors"])

    # ---------------------------------------
    # フィルタリング ロジック
    # ---------------------------------------
    display_data = data 

    if filter_genres:
        display_data = [d for d in display_data if d.get("genre") in filter_genres]

    if filter_colors:
        display_data = [d for d in display_data if d.get("color") in filter_colors]

    if search_query:
        display_data = [d for d in display_data if search_query.lower() in d.get("name", "").lower()]

    st.markdown(f"**表示中: {len(display_data)} 件** / 全 {len(data)} 件")
    st.divider()

    # ---------------------------------------
    # メインエリア：図鑑表示
    # ---------------------------------------
    if not display_data:
        if not data:
            st.info("👈 左のサイドバーから、最初のお店を登録してみましょう！")
        else:
            st.warning("条件に一致するお店が見つかりませんでした。")
    else:
        for entry in display_data:
            color_class = f"card-{entry.get('color', 'Black')}"
            
            criteria_html = ""
            for item in APP_CONFIG["criteria"]:
                # データがない場合の安全策
                val = entry.get(item["id"], "")
                
                # スライダー表示
                if item["type"] == "slider":
                    # 値がない場合は1とする
                    num_val = int(val) if val and str(val).isdigit() else 1
                    stars = "★" * num_val + "☆" * (item.get("max", 5) - num_val)
                    criteria_html += f"<div><strong>{item['label']}：</strong> <span style='color:#f1c40f'>{stars}</span></div>"
                
                # その他のテキスト項目
                else:
                    # 空の場合は "-" を表示
                    disp_val = val if val else "-"
                    criteria_html += f"<div><strong>{item['label']}：</strong> {disp_val}</div>"

            st.markdown(f"""
            <div class="card {color_class}">
                <a href="?confirm_delete={entry['id']}" target="_self" class="delete-btn" title="削除">✕</a>
                <div class="number">No.{entry.get('order', '-')}</div>
                <h3>{entry['name']} </h3>
                <div class="card-meta">{entry['genre']}</div>
                <div class="card-meta">訪問日：{entry['date']}</div>
                <a href="{entry['url']}" target="_blank" class="url-button">お店のサイトを開く</a>
                <hr style="margin: 10px 0; border:none; border-top:1px dashed rgba(255,255,255,0.3);">
                {criteria_html}
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()