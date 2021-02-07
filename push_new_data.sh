docker-compose exec ksql-datagen ksql-datagen schema=/data/retailv2.avro iterations=200 format=json topic=retail key=RetailId bootstrap-server=broker:9092
