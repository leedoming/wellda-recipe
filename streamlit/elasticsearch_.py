from elasticsearch import Elasticsearch
import pandas as pd

# Elasticsearch 연결
es = Elasticsearch("http://localhost:9200")

# Elasticsearch에 인덱스 생성
INDEX_NAME = "recipe1"
if not es.indices.exists(index=INDEX_NAME):
    body = {
        "settings": {
            "analysis": {
                "analyzer": {
                    "my_analyzer": {
                        "type": "custom",
                        "tokenizer": "nori_tokenizer"
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "url": {"type": "keyword"},
                "name": {"type": "keyword"},
                "img": {"type": "keyword"},
                "summary": {"type": "keyword"},
                "info1": {"type": "keyword"},
                "info2": {"type": "keyword"},
                "info3": {"type": "keyword"},
                "ingredients": {"type": "text", "analyzer": "my_analyzer"},
                "combined": {"type": "text", "analyzer": "my_analyzer"}
            }
        }
    }
    es.indices.create(index=INDEX_NAME, body=body)


# CSV 파일 읽기 및 Elasticsearch에 데이터 로드
def load_and_load_to_elasticsearch(file_path):
    data = pd.read_csv(file_path)
    for idx, row in data.iterrows():
        try:
            es.index(index=INDEX_NAME, body=row.to_dict(), op_type="create")  # 색인 중복 방지를 위해 op_type="create" 설정
        except Exception as e:
            print(f"문서 인덱싱 중 오류 발생: {e}")
            continue  # 문서 인덱싱 중 오류가 발생하면 해당 문서를 스킵하고 다음 문서로 이동


# 메인 함수
def main():
    # CSV 파일 경로
    csv_file_path = "F:dw-data/dw_recipes_fin1.csv"  # 여기에 본인의 CSV 파일 경로를 입력하세요.

    # CSV 파일이 있으면 Elasticsearch에 데이터 로드
    if csv_file_path:
        load_and_load_to_elasticsearch(csv_file_path)
        print("데이터가 Elasticsearch에 성공적으로 로드되었습니다.")


if __name__ == "__main__":
    main()
