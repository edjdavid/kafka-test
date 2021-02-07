# kafka-test

Test infrastructure for kafka
  - generate random data from `ksql-datagen` using the schema from [retail.avro](test_data/retail.avro)
  - extract data from kafka using kafka-connect s3 connector, using MinIO as s3 replacement
  - use kafka-connect transform to reformat data and to dump the messages as json on minio

Dashboard
  - Read json data directly from MinIO using Dask
  - Create dashboard using Plotly Dash ([dashboard.py]('dashboard/dashboard.py'))


## Installation

```
docker-compose up -d
```
If everything goes well, ksql-datagen will send 200 random messages which will be converted to json and stored to `retail-bucket` in MinIO

### Ports
 - 8900: Dashboard
 - 9000: MinIO Browser

 ## Usage

To push new data to kafka
 ```
 docker-compose exec ksql-datagen ksql-datagen schema=/data/retail.avro iterations=200 format=json topic=retail key=RetailId bootstrap-server=broker:9092
```

\* Use [retailv2.avro]('data/retailv2.avro') to push messages with an additional `ProductRating` field