docker network create elastic
docker run -d --name elasticsearch --net elastic -p 9200:9220 -p 9300:9300 -e "discovery.type=single-node" elasticsearch:8.12.0

docker ps -a #컨테이너 id 확인

#elasticsearch security false setting
docker cp ./elasticsearch.yml container_id:/usr/share/elasticsearch/config/elasticsearch.yml

#nori_tokenizer 설치
docker exec -it container_id ./bin/elasticsearch-plugin install analysis-nori

#data elasticsearch mapping
python3 elasticsearch_.py
