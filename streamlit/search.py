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
    res = es.search(index="recipe3", body=body1)
    return res["hits"]["hits"]

# ingredients 전처리 함수
def process_type1(data):
    return data.replace('\n', '').replace('dd', '').strip()

def recipe_engine():

    # row1.config
    row1_spacer1, row1_2, row1_spacer2 = st.columns(
        (3, 4, 3)
    )

    # row2.config
    row2_spacer1, row2_1, row2_spacer2, row2_2, row2_spacer3, row2_3 = st.columns(
        (.4, 1.6, .1, 1.6, .1, .4)
    )
    
    # 페이지 제목
    with row1_2:
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
                        st.write(f"요리명: {hit['_source']['RecipeName']}")
                        st.write(f"요리 소개: {hit['_source']['Summary']}")
                        steps = hit['_source']['Steps']
                        try:
                            # ingredients 문자열을 파싱하여 파이썬의 리스트로 변환
                            ingredients_list = eval(hit['_source']['Ingredients_pre'])
                            # 재료명만 추출하여 띄어쓰기로 구분하여 출력
                            ingredient_names =  ', '.join([ingredient['Ingredients_pre'] for ingredient in ingredients_list])
                        except(SyntaxError):
                            ingredients_list = hit['_source']['Ingredients_pre']
                            ingredient_names = process_type1(ingredients_list)

                        st.write(f"재료: {ingredient_names}")
                        # 텍스트를 줄 단위로 분리
                        lines = steps.strip().split("\n")

                        # 각 줄을 처리
                        for line in lines:
                            parts = line.split(", ")
                            for part in parts:
                                if part.startswith("https"):
                                    # 이미지 URL을 찾으면 이미지를 다운로드하고 출력
                                    response = requests.get(part)
                                    img = Image.open(BytesIO(response.content))
                                    # 이미지 설명을 표시
                                    st.write("Image Description:")
                                    # 이미지 표시
                                    st.image(img, caption='Image from URL')
                                else:
                                    st.write("검색 결과가 없습니다.")
