import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import *
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType
import hashlib
from dateutil.parser import parse

def hash_cc(s):
    return hashlib.sha256(s).hexdigest()

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

datasource0 = glueContext.create_dynamic_frame.from_catalog(database = "serverless-datalake", table_name = "user-profile", transformation_ctx = "datasource0")


## @convert glue DynamicFrame to DataFrame to manipulate the columns
dataframe0 = DynamicFrame.toDF(datasource0)

hash_cc_f = udf(lambda x: hash_cc(x), StringType())

dataframe0 = dataframe0.withColumn("hash_cc", hash_cc_f(dataframe0["cc"])).withColumn("hash_ssn", hash_cc_f(dataframe0["ssn"]))
dataframe0 = dataframe0.drop('cc').drop('ssn').drop('password')

## @convert dataframe to glue DynamicFrame and write the output in parquet format
datasource1 = DynamicFrame.fromDF(dataframe0, glueContext, "name1")


datasink4 = glueContext.write_dynamic_frame.from_options(frame = datasource1, connection_type = "s3", connection_options = {"path": "s3://serverless-datalake-ingestionbucket-1jiyskijz5i03/prepared/userprofile-secure"}, format = "parquet", transformation_ctx = "datasink4")

job.commit()