<script src="https://code.jquery.com/jquery-3.2.1.min.js"></script>
<script src="/workshop.js"></script>

# Serverless Data Lake Workshop
Welcome to the serverless data lake workshop. In this workshop, you will create a serverless data lake that combines the data from an ecommerce website, customer profile database, and demographic data.

<span id="test"></span>

## Backstory

You are playing the role of the data lake architect and your primary customers are the analytics and BI team for the ecommerce website. They want to learn about customer behaviors from a variety of data sources across the enterprise. The current data warehouse is too rigid and doesn't offer the flexibility to explore and visualize data across different silos within the enterprise. Your job is to work with the cloud engineering team, the teams that support the source systems, and the analytics team to give them the tools they need to help grow the business.

### Current Challenges

The current data warehouse is very rigid in its star schema architecture. It is very difficult to get new data into the warehouse and have it linked up to other data sources. The result is a set of data marts that are isolated from one another. Another challenge is that there is a lot of semi-structed data sources that the current data warehouse team cannot process. For example, data is pulled from the web log JSON files into a relational database, but only a subset of the data fits into the existing schema and the rest is lost. If the requirements change, it is very difficult and time consuming to change the schema, and the historical data is lost since the source files are not kept.

### The Cloud Engineering Team

The cloud engineering team has put together an set of resources that you can use to build out the datalake. They practice infrastructure as code, so all the components are created using a set of cloud formation scripts that are available in this git repository.

These resource include the basics of the data lake such as S3 buckets, as well as IAM roles that will be needed to access the services.

When a CloudFormation script completes execution, it returns a set of Outputs that provide details on the resources that were created. 

In order to complete the lab, you will need to be familiar with where to find these outputs and how to use them in the lab. Once you create the CloudFormation stack, spend a little time navigating the console to find these outputs.

### Why a Data Lake
A data lake is the central repository for all data in the enterprise. It ingests data from a variety of data sources and stores them in the lake in the format they arrive without losing data. ETL processes will transform the data into a prepared state, either as files optimized for query such as ORC or parquet, or into Redshift, an MPP Data warehouse with many nodes.

#### Separation of Data and Compute
Traditional data warehouses store data on database clusters that both store the data and perform the operations on the data. This leads to a challege as the dataset grows: Do you optimize your resources for compute or storage? 

By storing the data on Amazon S3, you have a cost-effective service that can store virtually unlimited amounts of data. Around S3 is an ecosystem of tools that enable direct querying of the data, or high performance loading into a database cluster. This also permits the creation of transient clusters that spin up to perform the computations and spin down when they are complete.

## Why Serverless
* Simple to manage
* No Cost for Idle
* Agile

# Setup
Here is the Amazon CloudFormation script that the cloud engineering team made available. <a href="https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review?templateURL=https://s3.amazonaws.com/arc326-instructions/script/serverless-data-lake.yaml" target="_blank">Create a stack</a> This template will provide a headstart in configuring the data lake.

## Serverless Data Lake Components
* S3
* DynamoDb
* Athena
* Lambda
* Kinesis Firehose
* Quicksight


<details><summary>Component Details</summary>
<p>

# Storage
The separation of data and compute is a foundation architectural concept in modern data lakes. By using S3 as the storage tier, you can have transient data warehouse or hadoop clusters that scale up to the compute capacity when you need them.

## Simple Storage Service (S3)
Amazon S3 is object storage built to store and retrieve any amount of data from anywhere – web sites and mobile apps, corporate applications, and data from IoT sensors or devices. It is designed to deliver 99.999999999% durability, and stores data for millions of applications used by market leaders in every industry.

S3 is the cornerstone of a data lake, it provides the storage tier for data at rest. Data in S3 can be queried in place using Athena or Redshift Spectrum, mounted to Hadoop with EMR, and loaded into Redshift.

## Amazon Redshift
Amazon Redshift is a fast, scalable data warehouse that makes it simple and cost-effective to analyze all your data across your data warehouse and data lake. Redshift delivers ten times faster performance than other data warehouses by using machine learning, massively parallel query execution, and columnar storage on high-performance disk.

Redshift is integrated with S3 to allow for high performance parallel data loads from S3 into Redshift. 

# Ingestion  

## Kinesis Data Firehose
Amazon Kinesis Data Firehose is the easiest way to load streaming data into data stores and analytics tools. It can capture, transform, and load streaming data into Amazon S3, Amazon Redshift, Amazon Elasticsearch Service, and Splunk, enabling near real-time analytics with existing business intelligence tools and dashboards you’re already using today. It is a fully managed service that automatically scales to match the throughput of your data and requires no ongoing administration. It can also batch, compress, and encrypt the data before loading it, minimizing the amount of storage used at the destination and increasing security.

## Relational Databases
Relational database systems form the backbone of most enterprise data systems. The data lake will receive data from the relational databases on a periodic basis, either through a data stream such as Kinesis Firehouse, 3rd-party tools like Sqoop, or through change data capture (CDC) using Amazon Satabase Migration Service (DMS). These data changes will be pushed into the ingestion buckets in the data lake for later processing. In this lab, we will copy data into S3 to simulate the ingestion of data from a CDC service like DMS. 

## Third Party Data
Frequently data that comes from outside the organization will be valuable to integrate into the data lake. In this example, demographic data from the US Census bureau will be included in the data for analysis. The data will be staged into S3 during startup by the CloudFormation script, but this data can be source through a variety of channels.

# Data Catalog
## Glue Data Catalog
The AWS Glue Data Catalog contains references to data that is used as sources and targets of your extract, transform, and load (ETL) jobs in AWS Glue. To create your data warehouse, you must catalog this data. The AWS Glue Data Catalog is an index to the location, schema, and runtime metrics of your data. The AWS Glue Data Catalog is Hive compatible so it can be used with Athena, EMR, and Redshift Spectrum in additoin to Glue ETL.

You can add table definitions to the AWS Glue Data Catalog in the following ways:
* Run a crawler that connects to one or more data stores, determines the data structures, and writes tables into the Data Catalog. You can run your crawler on a schedule.
* Use the AWS Glue console to create a table in the AWS Glue Data Catalog. 

</p>
</details>

# Ingestion
The first step in the data processing in a data lake is that data needs to land in S3.

The cloud engineering team has created an extract of the user profile database and demographic data into S3. They also were able to create entries in the Glue Data Catalog for this data. They accomplished this through some scripting, but they need help ingesting the web log data from the websites. The web logs are in a JSON format and they are unsure how to import the data into the Glue Data Catalog.

## Kinesis Firehouse Delivery Steam
Kinesis Firehouse provides a fully managed stream processing service that's highly scalable and can deliver data to S3. The application teams will publish the log files to cloudwatch logs via the cloudwatch agent. 

### Lab
This section requires outputs from the CloudFormation stack output. If the cloudformation stack has not yet completed, please wait until it has completed. Go to the CloudFormation <a href="https://us-east-1.console.aws.amazon.com/cloudformation/home" target="_blank">console</a> click the checkbox next to stack for this workshop and look for the 'Outputs' tab below. The key will be IngestionBucket and copy the value onto your clipboard. 


1. Under Services, Type 'Kinesis'
1. Under 'Kinesis Firehouse Delivery Streams', select 'Create Delivery Stream'
1. Provide a Delivery Stream Name: 'ecommerce-json-weblogs'
1. Source: Select 'Direct PUT or other sources'
1. Click Next
1. Record Transformation: 'Disabled'
1. Record format conversion: 'Disabled'
1. Click Next
1. Destination: Amazon S3
1. Provide the bucket name: This will be the IngestionBucket output value from the CloudFormation stack
1. Provide a prefix: 'weblogs/''
1. Click Next
1. Buffer size: 5
1. Buffer Interval: 300
1. S3 Compression: Disabled
1. S3 encryption: Disabled
1. Error Logging: Enabled
1. IAM Role: Click Create New or Choose
1. IAM Role: Select '**stackname**_weblog_delivery_role' *The cloud team created this role for you*
1. Policy Name: Select '**stackname**weblog_delivery_policy' *The cloud team created this policy for you*
1. Click 'Allow'
1. Click Next
1. Click 'Create Delivery Stream'


# Start Amar 


## Getting Started
Most of the times raw data is unstructured and inefficient for querying. In its raw format, Apache Weblogs structure is difficult to query. Also a lot of times there is always a need to transform the raw datasets by either augmenting or reducing the raw data to derive meaningful insights.
As part of this workshop we will start with creating the table definitions (schemas) from the raw datasets that we have:

- `useractivity.csv`
- `zipcode-adjustedgrossincome.csv`
- `userprofile DynamoDB table`

The datasets we'll be using for the workshop are downloaded into the S3 bucket at:
```
 s3://serverless-data-lake/raw
```
The `useractivity.csv` file contains data in CSV format like below:


ip_address	  | username   |	timestamp	     |       request	          |          http  |	bytes
--------------| ---------- | -------------------- | ------------------------- | -------------- | ---------
105.156.115.196 |	ontistesns0 |	17/Jan/2018:10:43:54 |	GET /petstore/Cats/Treats |	200 |	    314
57.143.147.52 |	agkgamyaar4 |	14/Jun/2018:06:39:54 |	GET /petstore/Fish/Food |	    200	 |    575
29.152.175.209 |	nealaoaaoc9 |	6/Jan/2018:06:51:54 |	    GET /petstore/Bird/Treats |	200	 |    419

The `zipcode-adjustedgrossincome.csv` file contains data in CSV format like below:

statefips | state | zipcode	 |  agi_stub  |   nbrreturns  |	totalagi
----------| ----- | -------- | ---------- | ------------- | ---------
1 |	AL |	35004 |	1 |	1510 |	    19675
8 |	CO |	80124 |	3 |	    1810	 |    68265
12 |	FL |	33954 |	    2 |	1310	 |    47741

The `userprofile` DynamoDB table contains data like below:

first_name | last_name | username |	email |	gender | ip_address | phone | zip |	cc | password |	ssn | age | 
---------| --- | ---- | ------ | ------------ | ----------- | ----------| ---------- | ------- | ------ | ---- | ---- |
Antonetta | Stills |ontistesns0 | AntonettaStills@gmail.com | F | 105.156.115.196 |	274-218-6653 |	76059 |	6835-5177-8166-5873 |	ettttoette6 |	116-48-1824 |	35
Maragret |	Katayama |	agkgamyaar4 |	MaragretKatayama@adobe.com |	F |	57.143.147.52 |	751-343-4134 |	82411 |	1353-4321-3472-8117 |	rgtyrraara6 |	211-26-5867 |	24
Lakendra |	Cacciola |	nealaoaaoc9 |	LakendraCacciola@nytimes.com | F |	29.152.175.209 |	552-251-2661 |	19086 |	4773-6731-7825-3365 |	ncirciCadr8 |	446-73-7861 |	61

### Crawl datasets to create table definitions

The first step is to crawl these datasets and put the results into a database called `weblogs` in your Data Catalog as described here in the [Developer Guide](https://docs.aws.amazon.com/glue/latest/dg/console-crawlers.html).
The crawler will create the following tables in the `weblogs` database:
- `useractivity_csv`
- `userprofile`
- `zipcode-adjustedgrossincome_csv`



#### Steps to create crawler for useractivity & zip-adjustedgrossincome

1. From AWS Management Console, in the search text box, type `AWS Glue`, select `AWS Glue` service from the filtered list to open AWS Glue console.
2. From `AWS Glue` dashboard, from left hand menu select `Crawlers` menu item
3. From `Crawlers` page, click `Add crawler` button
4. On `Crawler Info` wizard step, enter crawler name `rawdatacrawler`, keep the default on the page and click `Next` button
5. On `Data Store` step, choose S3 from `Choose a data store` drop down. Choose `s3://serverless-data-lake/raw` S3 bucket location from `Include path`. Keep other defaults the same and click `Next` button
6. Choose `No` and click `Next` on `Add another data store` 
7. On `IAM Role` step, choose `Choose an existing IAM role` option and select `AWSGlueServiceRoleDefault` from `IAM role` drop down. click `Next`
8. On `Schedule` step keep the default `Run on demand` option and click `Next`
9. On `Output` step, choose `weblogs` database from `Database` drop down. Keep default the same and click `Next` button
10. On `Review all steps` step, review the selections and click `Finish`. this should take to back to `Crawlers` dashboard
11. On `Crawlers` dashboard, select the crawler that you created in above steps and click `Run Crawler` button
12. The crawler will go into *Starting* to *Stopping* to *Ready*
13. Once the crawler is in *Ready* state, from left hand menu select `Databases`
14. From `Databases` page select *weblogs* database and select `Tables in weblogs` link. You should see two tables `useractvity` and `zipcode-adjustedgrossincome` listed.
15. From `Tables` page, select `useractvity` table and explore the table definition that glue crawler created.
16. From `Tables` page, select `zipcode-adjustedgrossincome` table and explore the table definition that glue crawler created.

#### Steps to create crawler for userprofile

1. From AWS Management Console, in the search text box, type `AWS Glue`, select `AWS Glue` service from the filtered list to open AWS Glue console.
2. From `AWS Glue` dashboard, from left hand menu select `Crawlers` menu item
3. From `Crawlers` page, click `Add crawler` button
4. On `Crawler Info` wizard step, enter crawler name `rawdatacrawler-dynamo`, keep the default on the page and click `Next` button
5. On `Data Store` step, choose *DynamoDB* from `Choose a data store` drop down. Choose `userprofile` DynamoDB table from `Table name` and click `Next` button
6. Choose `No` and click `Next` on `Add another data store` 
7. On `IAM Role` step, choose `Choose an existing IAM role` option and select `AWSGlueServiceRoleDefault` from `IAM role` drop down. click `Next`
8. On `Schedule` step keep the default `Run on demand` option and click `Next`
9. On `Output` step, choose `weblogs` database from `Database` drop down. Keep default the same and click `Next` button
10. On `Review all steps` step, review the selections and click `Finish`. this should take to back to `Crawlers` dashboard
11. On `Crawlers` dashboard, select the crawler that you created in above steps and click `Run Crawler` button
12. The crawler will go into *Starting* to *Stopping* to *Ready*
13. Once the crawler is in *Ready* state, from left hand menu select `Databases`
14. From `Databases` page select *weblogs* database and select `Tables in weblogs` link
15. From `Tables` page, select `userprofile` table and explore the table definition that glue crawler created.


### Data Flattening and format conversion

Once the `useractivity_csv`, `userprofile` and `zipcode-adjustedgrossincome_csv` table definitions are created, the next step is to create a glue job `useractivityjob`. In this job we will flatten the *request* and *timestamp* columns and convert to original file format from csv to compact, efficient format for analytics, i.e. Parquet. We will evaluate the query efficiencies in Athena based on source file formats. 

> Converted Table 


ip_address|username |timestamp | request|http | bytes |  requesttype|topdomain|toppage|subpage | date  | time
---- | ----| ------------ | ----------| ----| --------| ------------ | ------ | ------ | ----- | ------ | ----
105.156.115.196 |	ontistesns0 |	17/Jan/2018:10:43:54 |	GET /petstore/Cats/Treats |	200 |	    314 |   GET  |        petstore |   Cats  |  Treats | 17/Jan/2018 | 10:43:54 |  
57.143.147.52 |	agkgamyaar4 |	14/Jun/2018:06:39:54 |	GET /petstore/Fish/Food	|    200	|    575  |   GET    |     petstore  |  Fish  |  Food  |  14/Jun/2018  | 06:39:54
29.152.175.209 |	nealaoaaoc9 |	6/Jan/2018:06:51:54	 |   GET /petstore/Bird/Treats |	200	   | 419   |  GET    |     petstore |   Birds  | Treats  | 6/Jan/2018 | 06:51:54


#### Steps to create and execute glue job: useractivityjob
 As part of this step you will create a glue job, update the default script and run the job

1. From left hand menu select `Jobs` menu
2. From *Jobs* menu page, click `Add job` button
3. Follow the instructions in the `Add job` wizard
   - Under `Job properties` step, Enter *useractivityjob* in the `Name` text box
   - Under `IAM role` drop down select *AWSGlueServiceRoleDefault*
   - Keep rest of the default the same and click `Next` button
   - Under `Data source` step, choose `useractivity_csv` data catalog table and click `Next`  button
   - Under `Data target` step, choose `Create tables in your data target` option 
	 - Choose *Amazon S3* from `Data store` drop down
	 - Choose *Parquet* from `Format` drop down
	 - From `Target path` choose *serverless-data-lake/weblogs/useractivityconverted* S3 bucket and click `Next` button
   - Under `Schema` step, keep default and click `Next` button
   - Under `Review` step, review the selections and click `Save job and edit script` button
4. Under `Edit Script` step, based on the `Add Job` wizard selection, AWS Glue creates a PySpark script which you can edit and write your logic. The AWS Glue created code coverts the source data to parquet but does not flatten the request and timestamp. Let's update the code to add our custom logic to flatten the columns.
   - Select all the code under `Edit Script` replace it with below

``` python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import *
from awsglue.dynamicframe import DynamicFrame

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

datasource0 = glueContext.create_dynamic_frame.from_catalog(database = "weblogs", table_name = "useractivity_csv", transformation_ctx = "datasource0")

applymapping1 = ApplyMapping.apply(frame = datasource0, mappings = [("ip_address", "string", "ip_address", "string"), ("username", "string", "username", "string"), ("timestamp", "string", "timestamp", "string"), ("request", "string", "request", "string"), ("http", "long", "http", "long"), ("bytes", "long", "bytes", "long")], transformation_ctx = "applymapping1")

resolvechoice2 = ResolveChoice.apply(frame = applymapping1, choice = "make_struct", transformation_ctx = "resolvechoice2")

dropnullfields3 = DropNullFields.apply(frame = resolvechoice2, transformation_ctx = "dropnullfields3")

## @convert glue DynamicFrame to DataFrame to manipulate the columns
dataframe0 = DynamicFrame.toDF(applymapping1)

## @split request columns on '/' 
split_column = split(dataframe0['request'], '/')

dataframe0 = dataframe0.withColumn('requesttype', split_column.getItem(0))

dataframe0 = dataframe0.withColumn('topdomain', split_column.getItem(1))
dataframe0 = dataframe0.withColumn('toppage', split_column.getItem(2))
dataframe0 = dataframe0.withColumn('subpage', split_column.getItem(3))

## @convert dataframe to glue DynamicFrame and write the output in parquet format
datasource1 = DynamicFrame.fromDF(dataframe0, glueContext, "name1")

datasink4 = glueContext.write_dynamic_frame.from_options(frame = datasource1, connection_type = "s3", connection_options = {"path": "s3://serverless-data-lake/weblogs/useractivityconverted"}, format = "parquet", transformation_ctx = "datasink4")

job.commit()
```

   - Click `Save` button to save the changes
5. Select `Run job` button to execute the glue job, 
6. On `Parameters (optional)` dialog, keep the default and click `Run job` button
7. Select `X` from the right corner to close `Edit Script` page. This will take you back to `Jobs` dashboard
8. From jobs table select the job `userprofilejob` to open the detail tabs for the job.
9. Under `History` tab,, monitor the *Run status*. The *Run Status* column should go from "Running" to "Stopping" to "Succeeded"
10. Once the job is succeeded, go to S3 console and browse to `serverless-data-lake/weblogs/useractivityconverted` S3 bucket
11. Under the `useractivityconverted` S3 folder you should see parquet files created by the job

### Create a UDF to simplify apply a hash function to a columns
In order to protect sensative data, we will want to eliminate columns or hash sensitive fields. In this example we will hash user profile SSN's and credit card numbers. This will allow analysts to join profiles that share the same SSN or credit card, but encodes the sensitive data by applying a one-way hash algorith.

TO DO: 
* Add steps to create the job
* Replace the bucket name

``` python
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
```
	
### Serveless Analysis of data in Amazon S3 using Amazon Athena
Athena integrates with the AWS Glue Data Catalog, which offers a persistent metadata store for your data in Amazon S3. This allows you to create tables and query data in Athena based on a central metadata store available throughout your AWS account and integrated with the ETL and data discovery features of AWS Glue.
In this workshop we will leverage the AWs Glue Data Catalog `weblogs` for serverless analysis in Amazon Athena

#### Explore AWS Glue Data Catalog in Amazon Athena
1. From AWS Management Console, in the search text box, type `Amazon Athena`, select `Amazon Athena` service from the filtered list to open Amazon Athena console OR Open the [AWS Management Console for Athena](https://console.aws.amazon.com/athena/home).
2. If this is your first time visiting the AWS Management Console for Athena, you will get a Getting Started page. Choose Get Started to open the Query Editor. If this isn't your first time, the Athena Query Editor opens.
3. Make a note of the AWS region name, for example, for this lab you will need to choose the `US East (N. Virgina)` region.
4. In the `Athena Query Editor`, you will see a query pane with an example query. Now you can start entering your query in the query pane.
5. On left hand side of the screen, under `Database` drop down select `weblogs` database if not already selected. After selecting `weblogs` you should see 2 tables `useractivity_csv` and `zipcode_adjustedgrossincome_csv`
6. 


### 



# End Amar


<details><summary>Bonus</summary>
<p>Connect the cloudwatch logs to Kinesis Firehose. <a href="https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/SubscriptionFilters.html#FirehoseExample" target="_blank">More Info</a></p>
</details>

### Create a glue crawler

1. Open the Glue Data Catalog
1. Click 'Crawlers'
1. Click 'Add Crawler'
1. Supply a 'Crawler Name' with "User Profile"
1. Add a Descriptions (Optional)
1. Leave the security configuration to 'None'
1. Grouping (Leave Blank)
1. Click Next
1. Choose a data store: S3
1. Include Path: *This will be the IngestionBucket output value from the CloudFormation stack plus the prefix. ex: s3://stackname-ingestionbucket-abcdefgh012345678/weblogs*
1. Click Next
1. Add Another Store, select 'No'
1. Click Next
1. Choose an existing IAM Role: *stackname*-weblog-crawler
1. Frequency: Run on Demand
1. Choose a Database: *stackname*
1. Click Next
1. Click Finish
1. Look for the message: Crawler xxx was created to run on demand. Click 'Run it now?'

While the crawler is running, explore the other tables in this data lake.
1. Click the 'Databases' link of the left side navigation bar. T
1. Click the checkbox next to database with *stackname*. 
1. Click the 'View Tables' button near the top.
1. Explore the list of tables already in the catalog.

# View the Data
Now that the weblogs are available in Amazon S3, the analyics team would like access to the data. You'll use Amazon Athena to query the data using SQL Statements.

## Athena
Open the AWS Console and type 'Athena' in the service name textbox and select Athena.

In the Athena console, select *stackname* as the Database. The tables from the Glue Data Catalog will show in the left side navigation bar. Pick the *stackname-user-profile* table  and hit the icon of the 3 dots aligned vertically; from there, select 'Preview Table'.
Change the SQL statement to:

<code>SELECT COUNT(&#42;) FROM "serverless-datalake"."user-profile" limit 10;</code>

Note the amount of time for the query and the data read.


# Extract Transform Load (ETL)
The analytics team is happy to finally have access to the data, but it isn't performing well enough. They need to optimize the data for querying performance. This includes the following requirements:
* The data needs to be saved in a columnar format
* The data needs to be compressed
* Denormalization is required on data to improve query performance

## Athena Create Table as Select

The simplest way to convert a table into a more efficient format is to user the Athena Create Table as Select (CTAS) capability. It is as simple as running a query in Athena and providing the destination, file format, and partitioning information needed. Athena will add the new table to the glue data catalog, including the partition date.

1. In the Athena console, click create a new query, the + icon next to the query tab.
1. Copy and paste the following: <br/>
<pre><code>
CREATE TABLE IF NOT EXISTS userprofileparquet
  WITH (format='PARQUET', 
  		parquet_compression='SNAPPY', 
  		partitioned_by=ARRAY['gender'], 
  		external_location='s3://bucket-name/ctas-sample') AS
	SELECT id, 
		   first_name, 
		   last_name, 
		   username, 
		   email, 
		   ip_address, 
		   phone, 
		   zip, 
		   gender 
	FROM "serverless-datalake"."user-profile"
</code></pre>
1. Replace *bucketname* with the name of the ingestion bucket.

Once the query is run, you can look at the list of tables in Athena and see this table has been added, including the partitions.


## Glue ETL

While the CTAS functionality is great for simple transforms and aggregate functions, the Ecommerce analytics team would like to perform more advanced transforms on their data.

Glue ETL is a managed service that provides ETL capabilities in PySpark or Scala. This workshop will be running in the PySpark environment. The Glue ETL extends the PySpark DataFrame object into a DynamicFrame which provides additional transforms. [Additional Details]( https://docs.aws.amazon.com/glue/latest/dg/aws-glue-api-crawler-pyspark-extensions-dynamic-frame.html)

## Lab Exercise 
### Configure Zeppelin Notebook Server
**Note: Configuring a Zeppeling Server is optional in this workshop.**

We will provide the code needed to make the Glue jobs function properly. However, a notebook server makes the development of the glue scripts much more dynamic and it is strongly encourage to continue with this section.

#### Prerequisites
1. An AWS Keypair Generated in your account
1. A copy of the key downloaded to your computer. <a href="https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html" target="_blank"> More info</a>
1. SSH Client. 
  * Mac or Windows 10: Open a terminal window and type <code>ssh -i keypair.pem ec2-user@hostname</code>
    * If you get a permission denied error, make sure you set the permissions of the file using <code>chmod 400 keyfile.pem</code>
  * Pre-windows 10: 
    * Install PuTTY: <a href="https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/putty.html" target="_blank">More Info</a>
    * You will need to convert the pem file to a ppk file using the puttygen utility.

### Lab Activities
The cloud engineering team has created a development endpoint for you to build and develop your glue ETL scripts. A development endpoint is a glue service that allows you to run and test AWS Glue code without having to wait for servers to spin up and execute your job. This greatly reduces the frustration of debugging code having to wait for resources to become available.

The glue endpoint details are in the Output section of the cloudformation stack.

Go to the Glue Console and Select the Glue Development Endpoint created by the Cloud Engineering team.
1. Select Action->Create Zeppelin Notebook Server
1. Go through the Zeppelin Notebook Wizard
1. CloudFormation stack name: aws-glue-*stackname*
1. Select the role for this notebook server: *stackname*-notebook-role
1. KeyPair: Select the key pair from the prequisites
1. Attach a Public IP (True)
1. Notebook Username: Admin
1. Notebook S3 Path: s3://*ingestionbucket*/admin
1. Subnet: Pick a public subnet. Not sure which subnet is public? <a href="https://console.aws.amazon.com/vpc/home?region=us-east-1#subnets:sort=SubnetId" target="_blank">Subnet Console<a> Look at the Route Table tab of the subnet and see if the route to 0.0.0.0/0 starts with igw.
1. Click Finish. This will kick off a cloud formation script that builds out the notebook server.
1. After the notebook server is created, its status changes to CREATE_COMPLETE in the CloudFormation console. Example the Resources section and click the link by the 'Zeppelin Instance' resource.
1. Copy the Public DNS entry for the instance
1. Use your SSH client and connect to the instance. <code>ssh -i keyfile.pem ec2-user@paste-hostname-here</code>
1. From the home directory, run <code>./setup_notebook_server.py</code> **include the ./ to start the script** in ther terminal window. AWS Glue created and placed this script on the Amazon EC2 instance. The script performs the following actions:
  * **Type the password required to access your Zeppelin notebook**: Supply a password. You will need this password to open your Zeppelin server!
  * **Do you want a SSH key pair to be generated on the instance? WARNING this will replace any existing public key on the DevEndpoint**: Yes. Generates SSH public and private keys: The script overwrites any existing SSH public key on the development endpoint that is associated with the notebook server. As a result, any other notebook servers, Read–Eval–Print Loops (REPLs), or IDEs that connect to this development endpoint can no longer connect.
  * **Do you have a JKS keystore to encrypt HTTPS requests? If not, a self-signed certificate will be generated.**: No. This will create a self-signed certficate. You will need to put an exception in your browser to load the page.
1. Return to the Glue Console and click Notebooks or  <a href="https://console.aws.amazon.com/glue/home?region=us-east-1#etl:tab=notebooks" target="_blank">Click Here</a>
1. Click 'Zeppelin Notebook servers' tab.
1. Select your notebook server, under action select 'Open'
1. You will get an error due to a self-signed SSL certificate. This is expected. Depending on the browser, o make an exception.
1. In the upper right, click Login. User is 'admin' and password was supplied when configuring the notebook server.


### Supplimenting Data from Various Data Sources
A common example of preparing the data in a datalake is to denormalize data across distinct data sources. In this case, we will be adding geographical information into the HTTP request data by doing an IP lookup for the locations of each IP address in the web log files. This supplemented data will be saved in a Parquet format.
1. Locate the source data in the data catalog for the web logs and the IP lookup table.
1. Open the Zeppelin notebook for 'IPGeocoding'
1. Configure the changes in the Zeppelin Notebook.
1. Run the notebook to test the changes.

## Create the 

# Governance
Most large organizations will have different data classification tiers and a number of roles that have access to different classifications of data. With an S3 data lake, there are several ways to protect the data and grant access to the data.

The first layer will be to use IAM policies to grant access to IAM principles to the data in the S3 bucket. This is done with S3 bucket policies and IAM polices attached to IAM users, groups, and roles.

This approach is required if the consumer of the date requires direct access to the files or queries through Amazon Athena.

The second approach is to protect the data at the serving layer, which may be through an EMR cluster or Redshift cluster. With EMR, the cluster can authenticate users using Kerberos and Redshift can be authenticated using Redshift users or IAM credentials.

Finally, the Business Intelligence (BI) tier can authenticate users and limit visibility to reports and dashboards based on the user's group membership.

## Lab Exercise
It is common to have multiple classifications of data in the same table. One column will be more restricted than another. Because authorization in S3 is at the file level, you will need to separate out the restricted data from the less restricted data.


There are two approaches to this, the creation of two tables: one contains just the less sensitive data and other other contains the full dataset. In the less sensitive data, we have have the customer id, age, and a hash of the social security number. This will allow the Ecommerce analytics team to run demograhic analytics on the profiles and aggragate profiles of the same person via the hashed SSN.

The CustomerRestricted table will contain all of the columns.


| Customer | CustomerRestricted | 
| ------------- |:-------------:| 
| Customer ID | Customer ID |
| Age | Age |
| ZIP | ZIP |
| <Skip> | First Name |
| <Skip> | Last Name |
| SSN Hash | SSN |

1. Open the `Data Classification` notebook in Zeppelin. This will take the raw data from the customer profile and extract out the table into two tables.
1. Run the Glue Data Catalog Crawler to find the tables.
1. Create 2 new users, one has access, one does not
1. Run athena query against Customer with user1 and user2
1. Run athena query against CustomerRestricted with user1 and user2

