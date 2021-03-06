# kafka-test

Test infrastructure for kafka
  - generate random data from `ksql-datagen` using the schema from [retail.avro](test_data/retail.avro)
  - extract avro data from kafka using kafka-connect s3 connector, using MinIO as s3 replacement
  - use kafka-connect transform to reformat data and dump the messages as parquet on minio

SQL / Trino
  - Use parquet data in S3 as SQL data source (Table: `hive.retail.retail`)

Updating the schema
  - Update the Trino table schema


## Installation

```
docker-compose up -d
```
If everything goes well, ksql-datagen will send 100 random messages which will be converted to parquet and stored to `retail-bucket` in MinIO

### Ports
 - 8080: Trino
 - 9000: MinIO Browser

 ## Usage

To push new data to kafka
 ```
 docker-compose exec ksql-datagen ksql-datagen schema=/data/retail.avro iterations=200 format=json topic=retail key=RetailId bootstrap-server=broker:9092
```

\* Use [retailv2.avro]('data/retailv2.avro') to push messages with an additional `ProductRating` field