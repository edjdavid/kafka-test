docker-compose exec ksql-datagen ksql-datagen schema=/data/retailv2.avro \
iterations=50 format=avro topic=retail key=RetailId bootstrap-server=broker:9092 \
schemaRegistryUrl=http://schema-registry:8081
