import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
from elasticsearch import Elasticsearch

# Elasticsearch 연결
es = Elasticsearch("http://localhost:9200", timeout=90)

# Elasticsearch에서 레시피 검색 함수
def search_recipe(query):
    body1 = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["RecipeName^2", "Ingredients_pre^5", "Steps", "Summary"]
            }
        }
    }
    res = es.search(index="recipe1", body=body1)
    return res["hits"]["hits"]

# ingredients 전처리 함수
def process_type1(data):
    return data.replace('\n', '').replace('dd', '').strip()

# JSON 문자열 정리 함수
def clean_json_string(json_string):
    # 제어 문자를 제거
    json_string = re.sub(r'[\x00-\x1F\x7F]', '', json_string)
    return json_string

# 이미지 URL 수정 함수
def fix_image_url(url):
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
        # Elasticsearch에서 레시피 검색
        results = search_recipe(ingredients_input)
        
        # 검색 결과가 있을 경우
        if results:
            st.header("검색 결과")
            recipe_names = [hit['_source']['RecipeName'] for hit in results] # 레시피 이름 리스트 생성
            selected_recipe = st.selectbox("검색된 레시피 선택", recipe_names) # 레시피 선택
            
            # 선택한 레시피 정보 표시
            for hit in results:
                if hit['_source']['RecipeName'] == selected_recipe:
                    st.subheader("선택한 레시피")
                    st.image(hit['_source']['Image'], width=250, use_column_width='auto')
                    st.write("### 요리명")
                    st.write(f"{hit['_source']['RecipeName']}")
                    steps = hit['_source']['Steps']
                    try:
                        # ingredients 문자열을 파싱하여 파이썬의 리스트로 변환
                        ingredients_list = ast.literal_eval(hit['_source']['Ingredients_pre'])
                        # 재료명만 추출하여 띄어쓰기로 구분하여 출력
                        ingredient_names =  ', '.join([ingredient['Ingredients_pre'] for ingredient in ingredients_list])
                    except (ValueError, SyntaxError):
                        ingredients_list = hit['_source']['Ingredients_pre']
                        ingredient_names = process_type1(ingredients_list)
                    st.write("### 재료")
                    st.write(f"{ingredient_names}")
                    st.write("### 조리법")
                    # 텍스트를 줄 단위로 분리
                    lines = steps.strip().split("\n")

                    steps = ""
                    # 각 줄을 처리
                    for line in lines:
                        parts = line.split(", ")
                        print(parts)
                        for part in parts:
                            if part.startswith("http"):
                                pass
                            else:
                                st.write(part)
                                steps = steps + part
                    
                    st.markdown("---")

                    content = {
                        "title": hit['_source']['Steps'],
                        "ingredients": ingredient_names,
                        "steps": steps
                    }
                    if st.button("✅다이어트 레시피 변환", key=f"select_diet"):
                        st.session_state.diet_recipe_output = diet_recipe(content)
                        if st.session_state.diet_recipe_output:
                            selected_output = st.session_state.diet_recipe_output
                            clean_selected_output = clean_json_string(selected_output)
                            try:
                                # JSON 파싱
                                output_json = json.loads(clean_selected_output)
                                print(output_json)
                            except json.JSONDecodeError as e:
                                print(f"JSONDecodeError: {e}")

                            if output_json:
                                # 제목 표시
                                st.write("### 🍱요리명")
                                st.write(output_json.get('title', 'Title not available'))
                                
                                st.write("### 🥬재료")
                                # 재료 표시
                                st.write('✅' + output_json.get('ingredients', 'Ingredients not available'))
                                st.write("### 👨🏻‍🍳조리법")
                                # 조리법 표시
                                st.write('✅' + output_json.get('steps', 'Steps not available'))
                                else:
                                    st.write("검색 결과가 없습니다.")
