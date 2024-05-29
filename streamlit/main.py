import streamlit as st
import pandas as pd
import json
import requests
from recipe_create import diet_recipe, effect_create, extract_text
from search import recipe_engine
from urllib.parse import quote
import os
from PIL import Image
from io import BytesIO

# CSV 파일 열기
blog_df = pd.read_csv('../data/blog_.csv')

# JSON 파일 열기
with open('../data/output_0411.json', 'r', encoding='utf-8') as file:
    youtube_results = json.load(file)

# 블로그 데이터와 유튜브 데이터를 통합
results = []

# YouTube 데이터를 먼저 추가
for item in youtube_results:
    results.append({
        'type': 'youtube',
        'title': item['title'],
        'description': item['description'],
        'link': item['link'],
        'view': item.get('view', 'N/A'),
        'channel_title': item.get('channel_title', 'N/A')
    })

# 블로그 데이터 추가
for _, row in blog_df.iterrows():
    results.append({
        'type': 'blog',
        'title': row['title'],
        'description': row['content'],
        'link': row['link'],
        'thumbnail': row['img']
    })

def display_recipes(results, tab_type):
    st.header("SNS 다이어트 레시피 Trend🥬🥕")
    search_query = st.text_input("키워드 검색 시 관련 레시피만 보여져요🍳", "", key=f'search_{tab_type}')
    if search_query:
        results = [result for result in results if search_query.lower() in result["title"].lower()]
    
    if tab_type != "Common":
        results = [result for result in results if result['type'] == tab_type.lower()]
    
    if 'index' not in st.session_state:
        st.session_state.index = 0
    if 'selected_recipe' not in st.session_state:
        st.session_state['selected_recipe'] = None

    total_pages = (len(results) - 1) // 3 + 1
    page = st.slider("", 1, total_pages, st.session_state.index + 1, key=f'page_{tab_type}')
    st.session_state.index = page - 1

    start_index = st.session_state.index * 3
    end_index = start_index + 3
    end_index = min(end_index, len(results))

    for i, result in enumerate(results[start_index:end_index], start=start_index):
        with st.container():
            st.subheader(result["title"])
            col1, col2 = st.columns([2, 3])
            with col1:
                if result["type"] == "youtube":
                    video_link = result["link"].replace("/shorts/", "/embed/") if "/shorts/" in result["link"] else result["link"]
                    st.video(video_link)
                    st.markdown(
                        """
                        <style>
                        div[data-testid="stVideoContainer"] {
                            width: 600px !important;
                            height: 400px !important;
                        }
                        </style>
                        """,
                        unsafe_allow_html=True
                    )
                elif result["type"] == "blog":
                    if result['thumbnail']:
                        try:
                            # 이미지 URL
                            image_url = result["thumbnail"]
                            # URL에서 이미지 다운로드
                            response = requests.get(image_url)
                            image = Image.open(BytesIO(response.content))
                            # 이미지 표시
                            st.image(image, caption='Uploaded Image', use_column_width=True)
                        except:
                            image_response = requests.get(result['thumbnail'])
                            if image_response.status_code == 200:
                                image_path = f"./tmp_img_{i}_{tab_type}.jpg"
                                with open(image_path, 'wb') as file:
                                    file.write(image_response.content)
                                st.markdown(f"""
                                <div style="position: relative; width: 300px;">
                                    <button style="position: absolute; top: 10px; left: 10px; z-index: 100;" onclick="window.location.href='#'">✅선택</button>
                                    <img src="{image_path}" style="width: 100%;" />
                                </div>
                                """, unsafe_allow_html=True)

            with col2:
                if result["type"] == "youtube":
                    st.write(result["description"][:150] + '...')  # Display first 150 characters
                    st.markdown(f'조회수 {result["view"]}, 채널명 {result["channel_title"]}')
                    if col2.button("선택", key=f"select_{tab_type}_{i}"):
                        st.session_state.selected_recipe = result
                        video_id = result['link'].split('/')[-1].replace('-', '_').replace('.', '_')  # link에서 파일 이름 추출
                        script = extract_text(video_id)
                        content = {
                            "title": result["title"],
                            "description": result["description"],
                            "script": script
                        }
                        print(content)
                        st.session_state.selected_output = diet_recipe(content)
                        print(st.session_state.selected_output)
                elif result["type"] == "blog":
                    st.markdown(f"[{result['link']}]({result['link']})", unsafe_allow_html=True)
                    st.write(result["description"].split('\n')[0])
                    hashtags = [tag for tag in result["description"].split() if tag.startswith('#')]
                    st.markdown(" ".join(hashtags))
                    if col2.button("선택", key=f"select_{tab_type}_{i}"):
                        st.session_state.selected_recipe = result
                        content = {
                            "title": result["title"],
                            "content": result["description"]
                        }
                        st.session_state.selected_output = diet_recipe(content)

            st.markdown("---")

    if st.session_state.selected_recipe:
        selected_output = st.session_state.selected_output

        output_json = json.loads(selected_output)

        if output_json:
            # Display the title
            st.write(output_json.get('title', 'Title not available'))
            
            # Display the ingredients
            st.write(output_json.get('ingredients', 'Ingredients not available'))
            
            # Display the steps
            st.write(output_json.get('steps', 'Steps not available'))

def additional():
    ingredients = st.chat_input("재료를 입력하면 효능을 생성해드려요!")
    if ingredients:
        st.subheader(f'{ingredients}의 효능')
        st.write(effect_create(ingredients))
        st.image("https://via.placeholder.com/500", caption="Generated Image")

page = st.sidebar.selectbox("Choose your page", ["SNS Trends", "Recipe Search Engine"])
st.sidebar.markdown("""
    ## 페이지 설명
    **SNS Trend**
    * 유튜브, 블로그에서 일주일 간 인기 다이어트 레시피를 보여줍니다.\n
    **Recipe Engine**
    * 레시피 20만개 중 키워드 검색을 통해 관련 레시피를 보여줍니다.
    
    ## 기능 설명
    * 레시피를 선택 시, AI를 활용해 현업 레시피화 작업을 진행합니다.
    * 만약, 레시피 변환이 어려울 경우 unknown으로 답합니다.
    * 재료를 입력할 시, 해당 재료들을 기반으로 레시피 효능을 작성합니다.
    * 작성된 레시피를 기반으로 레시피 일러스트를 생성합니다.
""")
if page == "SNS Trends":
    tab = st.tabs(["Common", "YouTube", "Blog"])
    with tab[0]:
        display_recipes(results, "Common")
    with tab[1]:
        display_recipes(results, "YouTube")
    with tab[2]:
        display_recipes(results, "Blog")
    additional()
elif page == "Recipe Search Engine":
    recipe_engine()

# Cleanup downloaded images after rendering
for i in range(len(results)):
    image_path = f"./tmp_img_{i}.jpg"
    if os.path.exists(image_path):
        os.remove(image_path)
