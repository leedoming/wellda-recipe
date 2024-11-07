import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import ast
import json
import re
from couchbase.cluster import Cluster, ClusterOptions
from couchbase.auth import PasswordAuthenticator

# Couchbase 연결
def get_couchbase_connection():
    cluster = Cluster(
        'couchbase://localhost:8091',
        ClusterOptions(
            PasswordAuthenticator('Administrator', 'password')  # 실제 인증정보로 변경 필요
        )
    )
    bucket = cluster.bucket('recipes')
    return cluster, bucket

# Couchbase에서 레시피 검색 함수
def search_recipe(query):
    cluster, bucket = get_couchbase_connection()
    # N1QL 쿼리 작성
    search_query = f"""
        SELECT r.id, r.name as RecipeName, r.img as Image, 
               r.ingredients as Ingredients_pre, r.recipe_steps as Steps,
               r.summary
        FROM `recipes` r
        WHERE LOWER(r.name) LIKE LOWER($1)
           OR LOWER(r.summary) LIKE LOWER($1)
           OR ANY ingredient IN r.ingredients SATISFIES 
              LOWER(ingredient.ingre_name) LIKE LOWER($1) END
        LIMIT 10
    """
    
    # % 와일드카드를 사용하여 부분 일치 검색
    search_param = f"%{query}%"
    
    try:
        result = cluster.query(
            search_query,
            parameters=[search_param]
        )
        hits = []
        for row in result:
            hits.append({
                "_source": {
                    "RecipeName": row["RecipeName"],
                    "Image": row["Image"],
                    "Ingredients_pre": row["Ingredients_pre"],
                    "Steps": row["Steps"],
                    "Summary": row.get("summary", "")
                }
            })
        return hits
    except Exception as e:
        st.error(f"검색 중 오류가 발생했습니다: {str(e)}")
        return []

# ingredients 전처리 함수
def process_type1(data):
    return data.replace('\n', '').replace('dd', '').strip()

# JSON 문자열 정리 함수
def clean_json_string(json_string):
    return re.sub(r'[\x00-\x1F\x7F]', '', json_string)

# 이미지 URL 수정 함수
def fix_image_url(url):
    if not url:
        return url
    if not url.startswith("http"):
        url = "https://" + url
    if url.startswith("https //"):
        parts = url.split(" ", 1)
        url = parts[0] + ":" + parts[1]
    return url

def recipe_engine():
    st.write("""# 👩‍🍳키워드 입력을 통한 레시피 찾기""")
    st.write(' ')
    st.write(' ')
    # 사용자로부터 재료 입력 받기
    ingredients_input = st.text_input("음식, 재료 등 레시피 키워드를 입력하세요")

    # 사용자가 재료를 입력한 경우
    if ingredients_input:
        # Couchbase에서 레시피 검색
        results = search_recipe(ingredients_input)
        
        # 검색 결과가 있을 경우
        if results:
            st.header("검색 결과")
            recipe_names = [hit['_source']['RecipeName'] for hit in results]
            selected_recipe = st.selectbox("검색된 레시피 선택", recipe_names)
            
            # 선택한 레시피 정보 표시
            for hit in results:
                if hit['_source']['RecipeName'] == selected_recipe:
                    st.subheader("선택한 레시피")
                    image_url = fix_image_url(hit['_source']['Image'])
                    if image_url:
                        st.image(image_url, width=250, use_column_width='auto')
                    
                    st.write("### 요리명")
                    st.write(f"{hit['_source']['RecipeName']}")
                    steps = hit['_source'].get('Steps', {}).get('txt', '')
                    
                    try:
                        ingredients_list = hit['_source']['Ingredients_pre']
                        if isinstance(ingredients_list, str):
                            ingredients_list = json.loads(ingredients_list)
                        ingredient_names = ', '.join([ingredient.get('ingre_name', '') 
                                                   for ingredient in ingredients_list])
                    except (ValueError, SyntaxError, json.JSONDecodeError):
                        ingredient_names = process_type1(str(hit['_source']['Ingredients_pre']))
                    
                    st.write("### 재료")
                    st.write(f"{ingredient_names}")
                    st.write("### 조리법")
                    
                    if isinstance(steps, str):
                        lines = steps.strip().split("\n")
                        processed_steps = ""
                        for line in lines:
                            parts = line.split(", ")
                            for part in parts:
                                if not part.startswith("http"):
                                    st.write(part)
                                    processed_steps += part + "\n"
                    
                    st.markdown("---")

                    content = {
                        "title": hit['_source']['RecipeName'],
                        "ingredients": ingredient_names,
                        "steps": processed_steps
                    }
                    
                    if st.button("✅다이어트 레시피 변환", key=f"select_diet"):
                        st.session_state.diet_recipe_output = diet_recipe(content)
                        if st.session_state.diet_recipe_output:
                            selected_output = st.session_state.diet_recipe_output
                            clean_selected_output = clean_json_string(selected_output)
                            try:
                                output_json = json.loads(clean_selected_output)
                            except json.JSONDecodeError as e:
                                st.error(f"JSON 파싱 오류: {e}")
                                return

                            if output_json:
                                st.write("### 🍱요리명")
                                st.write(output_json.get('title', 'Title not available'))
                                
                                st.write("### 🥬재료")
                                st.write('✅' + output_json.get('ingredients', 'Ingredients not available'))
                                
                                st.write("### 👨🏻‍🍳조리법")
                                st.write('✅' + output_json.get('steps', 'Steps not available'))
                            else:
                                st.write("검색 결과가 없습니다.")
        else:
            st.write("검색 결과가 없습니다.")

if __name__ == "__main__":
    recipe_engine()