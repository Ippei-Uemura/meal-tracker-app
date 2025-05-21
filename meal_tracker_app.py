import streamlit as st
import pandas as pd
import os
from datetime import date

# ✅ 相対パスに修正
RECIPE_CSV = "recipes_db_utf8bom_complete.csv"
INGREDIENT_CSV = "ingredients_db_clinically_filtered_utf8bom.csv"
LOG_PATH = "daily_log.csv"

@st.cache_data
def load_data():
    if not os.path.exists(RECIPE_CSV) or not os.path.exists(INGREDIENT_CSV):
        st.error("CSVファイルが見つかりません。リポジトリ直下にファイルがあるか確認してください。")
        st.stop()
    recipes = pd.read_csv(RECIPE_CSV, encoding="utf-8-sig")
    ingredients = pd.read_csv(INGREDIENT_CSV, encoding="utf-8-sig")
    return recipes, sorted(ingredients["食材名"].dropna().unique().tolist())

recipes_df, ingredient_master = load_data()

page = st.sidebar.radio("ページを選んでください", ["🤖 メニュー提案", "🥗 記録", "📂 ログ閲覧"])

def score_recipe(input_ings, recipe_ings_str):
    recipe_ings = [i.strip() for i in str(recipe_ings_str).split(",")]
    score = 0
    for ing in input_ings:
        for r in recipe_ings:
            if ing == r:
                score += 2
            elif ing in r or r in ing:
                score += 1
    return score

if page == "🤖 メニュー提案":
    st.title("🤖 食材からメニュー提案（カテゴリ統合・柔軟マッチ）")

    selected_ingredients = st.multiselect("🥦 食材を選んでください", ingredient_master)
    free_input = st.text_input("✍️ 自由食材・調味料（カンマ区切り）")
    all_inputs = selected_ingredients + [i.strip() for i in free_input.replace("、", ",").split(",") if i.strip()]

    if st.button("💡 メニューを提案"):
        if not all_inputs:
            st.warning("少なくとも1つは食材を入力してください。")
        else:
            scored = recipes_df.copy()
            scored["score"] = recipes_df["ingredients"].apply(lambda x: score_recipe(all_inputs, x))
            results = scored[scored["score"] > 0].sort_values("score", ascending=False).head(5)
            if results.empty:
                st.markdown("（該当なし）")
            else:
                for _, row in results.iterrows():
                    st.markdown(f"**✅ {row['name']}（スコア：{row['score']}）**")
                    st.markdown("**【作り方】**")
                    for i in range(1, 4):
                        st.markdown(f"{i}. {row.get(f'step{i}', '')}")
                    st.markdown("---")

elif page == "🥗 記録":
    st.title("🥗 メニュー記録")
    menu_selected = st.selectbox("🍽️ 登録するメニューを選んでください", recipes_df["name"].tolist())
    record_date = st.date_input("🗓️ 日付", date.today())

    if st.button("📥 記録を保存"):
        df = pd.DataFrame([{"日付": record_date.isoformat(), "メニュー": menu_selected}])
        if os.path.exists(LOG_PATH):
            pd.concat([pd.read_csv(LOG_PATH), df], ignore_index=True).to_csv(LOG_PATH, index=False)
        else:
            df.to_csv(LOG_PATH, index=False)
        st.success("保存しました。")

elif page == "📂 ログ閲覧":
    st.title("📂 ログ閲覧・削除")
    if os.path.exists(LOG_PATH):
        log_df = pd.read_csv(LOG_PATH)
        st.dataframe(log_df)

        st.markdown("### 🗑️ 記録の削除")
        delete_target = st.selectbox("削除したい記録を選択", log_df.apply(lambda row: f"{row['日付']} - {row['メニュー']}", axis=1).unique())

        if st.button("❌ この記録を削除"):
            date_val, menu_val = delete_target.split(" - ")
            new_df = log_df[~((log_df["日付"] == date_val) & (log_df["メニュー"] == menu_val))]
            new_df.to_csv(LOG_PATH, index=False)
            st.success(f"{delete_target} を削除しました。")
            st.experimental_rerun()
    else:
        st.info("まだ記録がありません。")
