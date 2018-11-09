# Welcome to the AWS Serverless Data Lake Workshop

# Ingestion
The first step in the data processing in a data lake is that data needs to land in S3.

The cloud engineering team has created an extract of the user profile database and demographic data into S3. They also were able to create entries in the Glue Data Catalog for this data. They accomplished this through some scripting, but they need help ingesting the web log data from the websites. The web logs are in a CSV format and they are unsure how to import the data into the Glue Data Catalog.

The logs are be written to Cloudwatch logs and they have configured the subscription from cloud watch logs to kinesis firehouse. 


## Kinesis Firehouse Delivery Steam
Kinesis Firehouse provides a fully managed stream processing service that's highly scalable and can deliver data to S3. The application teams  publish the log files to cloudwatch logs via the cloudwatch agent. Currently, the logs are being published to the //*stackname*/apache CloudWatch Log Group.

### Lab
This section requires outputs from the CloudFormation stack output. If the cloudformation stack has not yet completed, please wait until it has completed. Go to the CloudFormation <a href="https://us-east-1.console.aws.amazon.com/cloudformation/home" target="_blank">console</a> click the checkbox next to stack for this workshop and look for the 'Outputs' tab below. The key will be IngestionBucket and copy the value onto your clipboard. 

We will verify that the log files are moving from the cloudwatch logs to the S3 bucket via Kinesis Firehouse.

**It may take a few minutes for data to show up in Kinesis**

1. Under Services, Type 'Kinesis'
1. Under 'Kinesis Firehouse Delivery Streams', select *stack name*-ApacheLogsKinesis-*random id*
1. Click the monitoring tab
1. Here you will see the delivery stream metrics.
1. **Incoming Bytes**: The amount of data ingested by the stream 
1. **Incoming Records**: The amount of records ingested by the stream 
1. **Execute Processing Duration**: The amount of time it takes to transform the data in the lambda function before it lands in S3.
1. **Execute Process Success**: The number of successful transformation calls by the stream 
1. **SucceedProcessing Records**: The number of records successfully processed.
1. **SucceedProcessing Bytes**: The amount of data successfully processed.
1. **DeliveryToS3 DataFreshness**: The age, in seconds, of the oldest record in the stream. All other data has been processed.
1. **DeliveryToS3 Success**: The number of files written to S3.
1. **DeliveryToS3 Records**: The number of records written to S3.
1. **DeliveryToS3 Bytes**: The number of bytes written to S3.
1. Click the Details Tab at the top.
1. Find the 'Amazon S3 destination' section and click the link for the S3 bucket.
1. Click 'weblogs'
1. Drill down into today's date & time and choose a file. The files will be stored in UTC time.
1. Click 'Open' and open the file in a text editor
1. It should contain the IP, username, timestamp, request path, and bytes downloaded.


<details><summary>Additional Details</summary>

There's a lot going on here and worth exploring. In reality, there is a lambda function generating the log data and writing it to cloud watch logs. Cloudwatch logs then has a Subscription Filter that will write any logs in the /*stackname*/apache log group to Kinesis Firehose.

You can see this configured in the CloudFormation script.
<code>
<pre>  CloudWatchLogsToKinesis:
    Type: AWS::Logs::SubscriptionFilter
    Properties: 
      DestinationArn: !Sub ${ApacheLogsKinesis.Arn}
      FilterPattern: ""
      LogGroupName: !Sub ${ApacheLogs}
      RoleArn: !Sub ${LogsToKinesisServiceRole.Arn}</pre>
</code>

The was done automatically in the lab because setting up the IAM Roles can be very tedious and time consuming.

Lastly, the logs written from CloudWatch to Kinesis are in a compressed JSON format. Not only are they they are harder to read in a compressed json format, aren't written in a JSON compliant format. Each line is a JSON file, but there aren't commas between each lines so JSON parsing fails. We use a template that will run a lambda function that uncompresses the file and returns the data payload which is in a CSV format.

</details>


# Extract, Transform and Load

Generally raw data is unstructured/semi-structured and inefficient for querying. In its raw format, Apache Weblogs are difficult to query. Also a lot of times there is always a need to transform the raw datasets by either augmenting or reducing the data to derive meaningful insights.
As part of this lab we will start with creating the table definitions (schemas) from the raw datasets that we have.
Below are the datasets that we would be working with:
- `useractivity.csv`
- `zipcodedata .csv`
- `userprofile.csv`

These datasets are downloaded into the S3 bucket at:

```
 s3://~ingestionbucket~/raw/useractivity
 s3://~ingestionbucket~/raw/userprofile
 s3://~ingestionbucket~/raw/zipcodes
```

## Create an IAM Role
Create an IAM role that has permission to your Amazon S3 sources, targets, temporary directory, scripts, AWSGlueServiceRole and any libraries used by the job. Refer [AWS Glue documentation](https://docs.aws.amazon.com/glue/latest/dg/create-an-iam-role.html) on how to create the role. For role permission make sure you select both AWS managed policy **AWSGlueServiceRole** for general AWS Glue permissions and the AWS managed policy **AmazonS3FullAccess** for access to Amazon S3 resources.

> In the Lab guide **AWSGlueServiceRoleDefault** role name is used. If you create the IAM role with a different name then please substitute your role name for **AWSGlueServiceRoleDefault**

## Discover Data

For this lab we will focus on weblogs data which is captured in `useractivity.csv` file. The data is in CSV format like below:


ip_address	  | username   |	timestamp	     |       request	          |          http  |	bytes
--------------| ---------- | -------------------- | ------------------------- | -------------- | ---------
105.156.115.196 |	ontistesns0 |	17/Jan/2018:10:43:54 |	GET /petstore/Cats/Treats |	200 |	    314
57.143.147.52 |	agkgamyaar4 |	14/Jun/2018:06:39:54 |	GET /petstore/Fish/Food |	    200	 |    575
29.152.175.209 |	nealaoaaoc9 |	6/Jan/2018:06:51:54 |	    GET /petstore/Bird/Treats |	200	 |    419


The second data set that we have is demographic data from `zipcodedata.csv` file. The data is in CSV format like below:


Zipcode | ZipCodeType | City	 |  State  |   LocationType  |	Lat | Long | Location | Decommisioned
----------| ----- | -------- | ---------- | ------------- | --------- | ---------- | ------------- | ---------
705 |	STANDARD |	AIBONITO |	PR |	PRIMARY |	18.14 |	-66.26 |	NA-US-PR-AIBONITO |	FALSE
610 |	STANDARD |	ANASCO |	PR |	PRIMARY	| 18.28 |	-67.14 |	NA-US-PR-ANASCO |	FALSE
611 |	PO BOX |	ANGELES |	PR |	PRIMARY	| 18.28	| -66.79 |	NA-US-PR-ANGELES |	FALSE
612 |	STANDARD |	ARECIBO |	PR |	PRIMARY |	18.45	| -66.73 |	NA-US-PR-ARECIBO |	FALSE


The third data set that we have is user profiles data in `userprofile.csv` file. The data is in CSV format like below:

first_name | last_name | username |	email |	gender |  phone | zip |	cc | password |	ssn | age | 
---------| --- | ---- | ------ | ------------ | ----------- | ----------| ---------- | ------- | ------ | ---- | 
Antonetta | Stills |ontistesns0 | AntonettaStills@gmail.com | F | 	274-218-6653 |	76059 |	6835-5177-8166-5873 |	ettttoette6 |	116-48-1824 |	35
Maragret |	Katayama |	agkgamyaar4 |	MaragretKatayama@adobe.com |	F |	751-343-4134 |	82411 |	1353-4321-3472-8117 |	rgtyrraara6 |	211-26-5867 |	24
Lakendra |	Cacciola |	nealaoaaoc9 |	LakendraCacciola@nytimes.com | F |	552-251-2661 |	19086 |	4773-6731-7825-3365 |	ncirciCadr8 |	446-73-7861 |	61


### Create Glue Data Catalog Database

1. From AWS Management Console, in the search text box, type **AWS Glue**, select **AWS Glue** service from the filtered list to open AWS Glue console OR Open the [AWS Management console for Amazon Glue](https://console.aws.amazon.com/glue/home?region=us-east-1).
2. To analyze the weblogs dataset, you start with a set of data in S3. First, you will create a database for this workshop within AWS Glue. A database is a set of associated table definitions, organized into a logical group.
3. From left hand menu of the AWS Glue console, click **Databases**
4. Click on the **Add Database** button.
5. Enter the Database name as `weblogs`. You can skip the description and location fields and click on **Create**.

### Crawl datasets to create table definitions

The first step is to crawl the datasets to create table definitions in Glue Data Catalog database `weblogs`. The table definitions will help us understand this unknown dataset, you will discover that the data is in different formats depending on the IT system that provided the data.

AWS Glue crawler will create the following tables in the `weblogs` database:
- `useractivity`
- `userprofile`

#### Steps to create crawler

1. From AWS Management Console, in the search text box, type **AWS Glue**, select **AWS Glue** service from the filtered list to open AWS Glue console OR Open the [AWS Management console for Amazon Glue](https://console.aws.amazon.com/glue/home?region=us-east-1).
2. From **AWS Glue** dashboard, from left hand menu select **Crawlers** menu item
3. From **Crawlers** page, click **Add crawler** button
4. On **Crawler Info** wizard step, enter crawler name `rawdatacrawler`, keep the defaults on the page the same and click **Next** button
5. On **Data Store** step, choose S3 from **Choose a data store** drop down. Choose `s3://~ingestionbucket~/raw` S3 bucket location from **Include path**.
5. Expand **Exclude patterns (optional)** section and enter `zipcodes/**` in **Exclude patterns** text box (We will exclude the zipcodes file in this exercise and pick it up latter in the lab). Click **Next** button
6. Choose **No** and click **Next** on **Add another data store**
7. On **IAM Role** step, choose **Choose an existing IAM role** option and select `AWSGlueServiceRoleDefault` from **IAM role** drop down. click **Next**
8. On **Schedule** step keep the default **Run on demand** option and click **Next**
9. On **Output** step, choose `weblogs` database from **Database** drop down. Keep defaults the same and click **Next** button
10. On **Review all steps** step, review the selections and click **Finish**. This should take to back to **Crawlers** dashboard
11. On **Crawlers** dashboard, select the crawler that you created in above steps and click **Run Crawler** button
12. The crawler will go into *Starting* to *Stopping* to *Ready* sate
13. Once the crawler is in *Ready* state, from left hand menu select **Databases**
14. From **Databases** page select *weblogs* database and select **Tables in weblogs** link. You should see two tables `useractvity` and `userprofile` listed.
15. From **Tables** page, select `useractvity` table and explore the table definition that glue crawler created.
16. From **Tables** page, select `userprofile` table and explore the table definition that glue crawler created.


### Data flattening and format conversion

Once the `useractivity` and `userprofile` table definitions are created, the next step is to create a glue job. In this job we will flatten the *request* and *timestamp* columns and convert the original file format from csv to compact, efficient format for analytics, i.e. Parquet. We will evaluate the query efficiencies in Athena based on source file formats. 

The converted table will look like below:

ip_address|username |timestamp | request|http | bytes |  requesttype|topdomain|toppage|subpage | date  | time | year | month
---- | ----| ------------ | ----------| ----| --------| ------------ | ------ | ------ | ----- | ------ | ---- | ---- | ----
105.156.115.196 |	ontistesns0 |	17/Jan/2018:10:43:54 |	GET /petstore/Cats/Treats |	200 |	    314 |   GET  |        petstore |   Cats  |  Treats | 17/Jan/2018 | 10:43:54 | 2018 | 1 
57.143.147.52 |	agkgamyaar4 |	14/Jun/2018:06:39:54 |	GET /petstore/Fish/Food	|    200	|    575  |   GET    |     petstore  |  Fish  |  Food  |  14/Jun/2018  | 06:39:54 | 2018 | 6
29.152.175.209 |	nealaoaaoc9 |	6/Jan/2018:06:51:54	 |   GET /petstore/Bird/Treats |	200	   | 419   |  GET    |     petstore |   Birds  | Treats  | 6/Jan/2018 | 06:51:54 | 2018 | 1


#### Steps to create glue job
 As part of this step you will create a glue job, update the default script and run the job. We will be using the AWS Management Console to write and edit the glue scripts but you also have an option of creating a `DevEndpoint` and run your code there. To create the `DevEndpoint` you can either refer **Configure Zeppelin Notebook Server** section of this lab guide or refer [AWS Glue documentation](https://docs.aws.amazon.com/glue/latest/dg/dev-endpoint.html)

 > If you are using Zeppelin Notebook then jump to step 4, create a new note `useractivityjob` and copy paste the code from step 4. Confirm spark as the **Default Interpreter**.

1. From AWS Management Console, in the search text box, type **AWS Glue**, select **AWS Glue** service from the filtered list to open AWS Glue console OR Open the [AWS Management console for Amazon Glue](https://console.aws.amazon.com/glue/home?region=us-east-1).
1. From AWS Glue dashboard left hand menu select **Jobs** menu
2. From **Jobs** menu page, click **Add job** button
3. Follow the instructions in the **Add job** wizard
   - Under **Job properties** step, Enter `useractivityjob` in the **Name** text box
   - Under **IAM role** drop down select `AWSGlueServiceRoleDefault`
   - Keep rest of the defaults the same and click **Next** button
   - Under **Data source** step, choose `useractivity` data catalog table and click **Next**  button
   - Under **Data target** step, choose **Create tables in your data target** option 
	 - Choose `Amazon S3` from **Data store** drop down
	 - Choose `Parquet` from **Format** drop down
	 - From **Target path** choose `~ingestionbucket~/weblogs/useractivityconverted` S3 bucket and click **Next** button
   - Under **Schema** step, keep default and click **Next** button
   - Under **Review** step, review the selections and click **Save job and edit script** button
4. Under **Edit Script** step, based on the **Add Job** wizard selection, AWS Glue creates a PySpark script which you can edit to write your logic. The system created code coverts the source data to parquet but does not flatten the request and timestamp. Let's update the code to add our custom logic to flatten the columns.
   - Select all the code under **Edit Script** page replace it with below

> ***Replace the S3 bucket path in the script below with your S3 bucket path***

``` python
## @ Import the AWS Glue libraries, pySpark we'll need 
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

## @ set up a single GlueContext.
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

## @ create the Glue DynamicFrame from table schema. A DynamicFrame is similar to a DataFrame, except that each record is 
## @ self-describing, so no schema is required initially.
useractivity = glueContext.create_dynamic_frame.from_catalog(database = "weblogs", table_name = "useractivity", transformation_ctx = "useractivity")

## @ ApplyMapping is one of the built in transfomrs that maps source columns and data types from a DynamicFrame to target columns 
## @ and data types in a returned DynamicFrame. You specify the mapping argument, which is a list of tuples that contain source column,
## @ source type, target column, and target type.
useractivityApplyMapping = ApplyMapping.apply(frame = useractivity, mappings = [("ip_address", "string", "ip_address", "string"), ("username", "string", "username", "string"), ("timestamp", "string", "timestamp", "string"), ("request", "string", "request", "string"), ("http", "long", "http", "long"), ("bytes", "long", "bytes", "long")], transformation_ctx = "applymapping1")

## @ ResolveChoice is another built in transform that you can use to specify how a column should be handled when it contains values of 
## @ multiple types. You can choose to either cast the column to a single data type, discard one or more of the types, or retain all 
## @ types in either separate columns or a structure. You can select a different resolution policy for each column or specify a global 
## @ policy that is applied to all columns.
resolvechoice2 = ResolveChoice.apply(frame = useractivityApplyMapping, choice = "make_struct", transformation_ctx = "resolvechoice2")

## @ DropNullFields tansform removes null fields from a DynamicFrame. The output DynamicFrame does not contain fields of the null type
## @ in the schema.
useractivity = DropNullFields.apply(frame = resolvechoice2, transformation_ctx = "dropnullfields3")

## @ We will leverage PySpark functions to manipulate our data, starting with converting glue DynamicFrame to DataFrame
dataframe0 = DynamicFrame.toDF(useractivity)

## @ Use PySpark functions to split request columns on '/' 
split_column = split(dataframe0['request'], '/')

dataframe0 = dataframe0.withColumn('requesttype', split_column.getItem(0))

dataframe0 = dataframe0.withColumn('topdomain', split_column.getItem(1))
dataframe0 = dataframe0.withColumn('toppage', split_column.getItem(2))
dataframe0 = dataframe0.withColumn('subpage', split_column.getItem(3))

## @ split timesstamp column into date, time, year and mnoth
dataframe0 = dataframe0.withColumn('date',date_format(from_unixtime(unix_timestamp('timestamp', 'd/MMM/yyyy:HH:mm:ss')), 'MM/dd/yyy'))
dataframe0 = dataframe0.withColumn('time',date_format(from_unixtime(unix_timestamp('timestamp', 'd/MMM/yyyy:HH:mm:ss')), 'HH:mm:ss'))

dataframe0 = dataframe0.withColumn('year', year(from_unixtime(unix_timestamp('timestamp', 'd/MMM/yyyy:HH:mm:ss'))))
dataframe0 = dataframe0.withColumn('month', month(from_unixtime(unix_timestamp('timestamp', 'd/MMM/yyyy:HH:mm:ss'))))


## @ convert dataframe to glue DynamicFrame and write the output in parquet format partitioned on toppapge column
useractivity = DynamicFrame.fromDF(dataframe0, glueContext, "name1")

writeUseractivityToS3 = glueContext.write_dynamic_frame.from_options(frame = useractivity, connection_type = "s3", connection_options = {"path": 's3://~ingestionbucket~/weblogs/useractivityconverted', "partitionKeys" :["toppage"]}, format = "parquet", transformation_ctx = "writeUseractivityToS3")

job.commit()
```

   - Click **Save** button to save the changes

5. Select **Run job** button to execute the glue job, 
6. On **Parameters (optional)** dialog, keep the default and click **Run job** button. You can see the job log in the lower half of the screen or on Glue Job dashboard.
7. Select **X** from the top-right corner to close **Edit Script** page. This will take you back to **Jobs** dashboard
8. From jobs table select the job `useractivityjob` to open the detail tabs for the job.
9. Under **History** tab, monitor the **Run status**. The **Run Status** column should go from *Running* to *Stopping* to *Succeeded*
10. Once the job is succeeded, go to S3 console and browse to `~ingestionbucket~/weblogs/useractivityconverted` S3 bucket
11. Under the `useractivityconverted` S3 folder you should see parquet files created by the job, partitioned by `toppage` column.

#### Explore the new dataset that we created in previous step

1. From AWS Management Console, in the search text box, type **AWS Glue**, select **AWS Glue** service from the filtered list to open AWS Glue console OR Open the [AWS Management console for Amazon Glue](https://console.aws.amazon.com/glue/home?region=us-east-1).
2. From **AWS Glue** dashboard, from left hand menu select **Crawlers** menu item
3. From **Crawlers** page, click **Add crawler** button
4. On **Crawler Info** wizard step, enter crawler name `useractivityconvertedcrawler`, keep the default on the page and click **Next** button
5. On **Data Store** step, choose S3 from **Choose a data store** drop down. Choose `s3://~ingestionbucket~/weblogs/useractivityconverted` S3 bucket location from **Include path**. Keep other defaults the same and click **Next** button
6. Choose **No** and click **Next** on **Add another data store** 
7. On **IAM Role** step, choose **Choose an existing IAM role** option and select `AWSGlueServiceRoleDefault` from **IAM role** drop down. click **Next**
8. On **Schedule** step keep the default **Run on demand** option and click **Next**
9. On **Output** step, choose `weblogs` database from **Database** drop down. Keep default the same and click **Next** button
10. On **Review all steps** step, review the selections and click **Finish**. this should take to back to **Crawlers** dashboard
11. On **Crawlers** dashboard, select the crawler that you created in above steps and click **Run Crawler** button
12. The crawler will go into *Starting* to *Stopping* to *Ready* state
13. Once the crawler is in *Ready* state, from left hand menu select **Databases**
14. From **Databases** page select `weblogs` database and select **Tables in weblogs** link. You should see 3 tables `useractvity`, `userprofile` and `useractivityconverted` listed.
15. From `Tables` page, select `useractivityconverted` table and explore the table definition that glue crawler created.

	
# Serveless Analysis of data in Amazon S3 using Amazon Athena

> If you are using Amazon Athena for the first then follow the [Setting Up Amazon Athena](https://docs.aws.amazon.com/athena/latest/ug/setting-up.html) to make sure you have the correct permissions to execute the lab.

Athena integrates with the AWS Glue Data Catalog, which offers a persistent metadata store for your data in Amazon S3. This allows you to create tables and query data in Athena based on a central metadata store available throughout your AWS account and integrated with the ETL and data discovery features of AWS Glue.
In this workshop we will leverage the AWs Glue Data Catalog `weblogs` for serverless analysis in Amazon Athena

> **Note:** In regions where AWS Glue is supported, Athena uses the AWS Glue Data Catalog as a central location to store and retrieve table metadata throughout an AWS account.

### Explore AWS Glue Data Catalog in Amazon Athena
1. From AWS Management Console, in the search text box, type **Amazon Athena**, select **Amazon Athena** service from the filtered list to open Amazon Athena console OR Open the [AWS Management Console for Athena](https://console.aws.amazon.com/athena/home).
2. If this is your first time visiting the AWS Management Console for Athena, you will get a Getting Started page. Choose **Get Started** to open the Query Editor. If this isn't your first time, the Athena Query Editor opens.
3. Make a note of the AWS region name, for example, for this lab you will need to choose the **US East (N. Virgina)** region.
4. In the **Athena Query Editor**, you will see a query pane with an example query. Now you can start entering your query in the query pane.
5. On left hand side of the screen, under **Database** drop down select `weblogs` database if not already selected. After selecting `weblogs` you should see tables `useractivity`, `userprofile` and `useractivityconverted` listed.

### Quering data from Amazon S3
Now that you have created the tables, you can run queries on the data set and see the results in AWS Management Console for Amazon Athena.

1. Choose **New Query**, copy the following statement into the query pane, and then choose **Run Query**.

```SQL
SELECT count(*) as TotalCount FROM "weblogs"."useractivity" where request like '%Dogs%';

```

Results for the above query look like the following: 

  | TotalCount |
  | ------  | 
  |	2064987 |

> **Note:** The current format is CSV and this query is scanning ~675MB of data and takes ~ 3.2 seconds to execute


2. Make a note of query execution time for later comparison while querying the data set in Apache Parquet format.
3. Choose **New Query** or click **+**, copy the following statement into the query pane, and then choose **Run Query** to query for the number of hits per user per page

```SQL
SELECT
  "y"."username" "username"
, "y"."request" "request"
, "max"("y"."requests") "hits"
FROM
  (
   SELECT
     "username"
   , "request"
   , "count"("request") "requests"
   FROM
    useractivity  
   GROUP BY "username", "request"
   ORDER BY "username" ASC
)  y
where "y"."request" like '%Dogs%'
GROUP BY "y"."username", "y"."request"

```

Results for the above query look like the following: 

username |	request |	hits
--------- | ------- | ----
aaaaaahtac7 |	"GET /petstore/Dogs/DryFood" |	4
aaaaaihrai7 |	"GET /petstore/Dogs/FoodToppers" |	13
aaaadwdaba2 |	"GET /petstore/Dogs/FoodToppers" |	6

> **Note:** The current format is CSV and this query is scanning ~675MB of data and takes ~5 seconds to execute


### Querying partitioned data using Amazon Athena

By partitioning your data, you can restrict the amount of data scanned by each query, thus improving performance and reducing cost. Athena leverages Hive for partitioning data. You can partition your data by any key. A common practice is to partition the data based on time, often leading to a multi-level partitioning scheme. For our weblogs data will have partitioned it by `request` as we want to understand the number of hits a user makes for a given `toppage`

1. Choose **New Query*** or **+**, copy the following statement into the query pane, and then choose **Run Query** to get the total number of hits for Dog products

```SQL
SELECT count(*) as TotalCount FROM "weblogs"."useractivityconverted" where toppage = 'Dogs';

```
Results for the above query look like the following: 

  | TotalCount |
 | ------   |
  |	2064987 |

> **Note:** This query executes much faster because the data set is partitioned and it in optimal format - Apache Parquet (an open source columnar). The amount of data scanned is 0KB and it takes ~1.5 seconds to execute. Athena charges you by the amount of data scanned per query. You can save on costs and get better performance if you partition the data, compress data, or convert it to columnar formats such as Apache Parquet.

2. Choose **New Query** or **+**, copy the following statement into the query pane, and then choose **Run Query** to get the total number of hits per user per request

```SQL
SELECT
 username, 
 toppage, 
 count(toppage) as hits
FROM useractivityconverted 
where toppage = 'Dogs'
GROUP BY username, toppage

```

Results for the above query look like the following: 

username |	toppage |	hits
-------- | ----- | ---
sossepepsl0 |	Dogs |	5
etraglhwaa0 |	Dogs |	21
anpnlrpnlm9 |	Dogs |	12

> **Note:** This query executes on partitioned parquet format data, the amount of data scanned is only ~750KB and it takes ~2.6 seconds to execute. Athena charges you by the amount of data scanned per query. You can save on costs and get better performance if you partition the data, compress data, or convert it to columnar formats such as Apache Parquet.

# Join and relationalize data with AWS Glue

In previous sections we looked how to work with semi-structured datasets to make it easily querable and consumable. In real world hardly anyone works with just one dataset. Normally you would end up working with multiple datasets from various datasources having different schemas. 
In this exerise we will see how you can leverage AWS Glue to join different datasets to load, transform, and rewrite data in AWS S3 so that it can easily and efficiently be queried and analyzed.
You will work with `useractivity` and `userprofile` datasets, the table definitions for which were created in previous section

### Create AWS Glue job 

 > If you are using Zeppelin Notebook then jump to step 4, create a new note `joindatasetsjob` and copy paste the code from step 4. Confirm spark as the **Default Interpreter**.

1. From AWS Management Console, in the search text box, type **AWS Glue**, select **AWS Glue** service from the filtered list to open AWS Glue console OR Open the [AWS Management Console for AWS Glue](https://console.aws.amazon.com/glue/home).
2. From **Jobs** menu page, click **Add job** button
3. Follow the instructions in the **Add job** wizard
   - Under **Job properties** step, Enter `joindatasetsjob` in the **Name** text box
   - Under **IAM role** drop down select `AWSGlueServiceRoleDefault`
   - Keep rest of the default the same and click **Next** button
   - Under **Data source** step, choose `useractivity` data catalog table and click **Next**  button
   - Under **Data target** step, choose **Create tables in your data target** option 
	 - Choose **Amazon S3** from **Data store** drop down
	 - Choose **Parquet** from **Format** drop down
	 - From **Target path** choose `~ingestionbucket~/weblogs/joindatasets` S3 bucket and click **Next** button
   - Under **Schema** step, keep default and click **Next** button
   - Under **Review** step, review the selections and click **Save job and edit script** button
4. Under **Edit Script** step, based on the **Add Job** wizard selection, AWS Glue creates a PySpark script which you can edit to write your logic. The AWS Glue created code coverts the source data to parquet but does not flatten the request and timestamp. Let's update the code to add our custom logic to flatten the columns.
   - Select all the code under **Edit Script** replace it with below and click **Save** button to save the changes

> Replace the S3 bucket path in the script below with your S3 bucket path

```python
## @ Import the AWS Glue libraries, pySpark we'll need 
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

## @ useractivity dynamicframe
useractivity = glueContext.create_dynamic_frame.from_catalog(database = "weblogs", table_name = "useractivity", transformation_ctx = "useractivity")

## @ applymappings to the dynamicframe to make sure we have the correct data types and column names
applymapping1 = ApplyMapping.apply(frame = useractivity, mappings = [("ip_address", "string", "ip_address", "string"), ("username", "string", "username", "string"), ("timestamp", "string", "timestamp", "string"), ("request", "string", "request", "string"), ("http", "long", "http", "long"), ("bytes", "long", "bytes", "long")], transformation_ctx = "applymapping1")

## @ resolve any issues with column data types
resolvechoice2 = ResolveChoice.apply(frame = applymapping1, choice = "make_struct", transformation_ctx = "resolvechoice2")

## @ drop any null fields
useractivity = DropNullFields.apply(frame = resolvechoice2, transformation_ctx = "useractivity")

## @ create userprofile dynamicframe
userprofile = glueContext.create_dynamic_frame.from_catalog(database="weblogs", table_name="userprofile")

## @ we will only keep the fields that we want and drop the rest and rename username to dy_username
userprofile = userprofile.drop_fields(['cc', 'password', 'ssn', 'email', 'phone','ip_address'])
userprofile = userprofile.rename_field('username','dy_username')

## @ as the data types in different datasets are different we are going to convert all column to string
## @ The Glue build in transform ApplyMapping, Maps source columns and data types from a DynamicFrame to target columns and data types 
## @ in a returned DynamicFrame. You specify the mapping argument, which is a list of tuples that contain source column, source type, 
## @ target column, and target type. In below case we are converting the data types for zip and age to string and updating the column
## @ names for first_name & last_name
userprofile = ApplyMapping.apply(frame = userprofile, 
mappings = [("first_name", "string", "firstname", "string"), 
("dy_username", "string", "dy_username", "string"), 
("zip", "bigint", "zip", "string"), 
("age", "bigint", "age", "string"), 
("gender", "string", "gender", "long"),
("last_name", "string", "lastname", "long")
], transformation_ctx = "userprofile")

## @join useractivity and userprofile datasets to create one file and drop the duplicate column dy_username
joined = Join.apply(userprofile, useractivity, 'dy_username', 'username').drop_fields(['dy_username'])

glueContext.write_dynamic_frame.from_options(frame = joined,
          connection_type = "s3",
          connection_options = {"path": 's3://~ingestionbucket~/weblogs/joindatasets'},
          format = "parquet")

job.commit()

```

5. Select **Save** button to save the glue job, 
5. Select **Run job** button to execute the glue job, 
6. On **Parameters (optional)** dialog, keep the default and click **Run job** button
7. Select **X** from the right corner to close **Edit Script** page. This will take you back to **Jobs** dashboard
8. From jobs table select the job `joindatasetsjob` to open the detail tabs for the job.
9. Under **History** tab, monitor the *Run status*. The *Run Status* column should go from "Running" to "Stopping" to "Succeeded"
10. Once the job is succeeded, go to S3 console and browse to `~ingestionbucket~/weblogs/joindatasets` S3 bucket
11. Under the `joindatasets` S3 folder you should see parquet files created by the job

#### Explore the new dataset created in previous step 

1. From AWS Management Console, in the search text box, type **AWS Glue**, select **AWS Glue** service from the filtered list to open AWS Glue console OR Open the [AWS Management Console for AWS Glue](https://console.aws.amazon.com/glue/home).
2. From **AWS Glue** dashboard, from left hand menu select **Crawlers** menu item
3. From **Crawlers** page, click **Add crawler** button
4. On **Crawler Info** wizard step, enter crawler name `joindatasetscrawler`, keep the default on the page and click **Next** button
5. On **Data Store** step, choose S3 from **Choose a data store** drop down. Choose `s3://~ingestionbucket~/weblogs/joindatasets` S3 bucket location from **Include path**. Keep other defaults the same and click **Next** button
6. Choose **No** and click **Next** on **Add another data store** 
7. On **IAM Role** step, choose **Choose an existing IAM role** option and select `AWSGlueServiceRoleDefault` from **IAM role** drop down. click **Next**
8. On **Schedule** step keep the default **Run on demand** option and click **Next**
9. On **Output** step, choose `weblogs` database from **Database** drop down. Keep default the same and click **Next** button
10. On **Review all steps** step, review the selections and click **Finish**. this should take to back to **Crawlers** dashboard
11. On **Crawlers** dashboard, select the crawler that you created in above steps and click **Run Crawler** button
12. The crawler will go into *Starting* to *Stopping* to *Ready* state
13. Once the crawler is in *Ready* state, from left hand menu select **Databases**
14. From **Databases** page select `weblogs` database and select **Tables in weblogs** link. You should see table `joindatasets` listed along with previously created tables.
15. From **Tables** page, select `joindatasets` table and explore the table definition that glue crawler created.

# Serveless Analysis of data in Amazon S3 using Amazon Athena Contd.
In previous sections we saw how Athena can leverage AWS Glue Data Catalog. In this section we will explore how you can create new table schema in Athena but still use the same AWS Glue Data Catalog.When you create a new table schema in Athena, Athena stores the schema in a data catalog and uses it when you run queries.Athena uses an approach known as schema-on-read, which means a schema is projected on to your data at the time you execute a query. This eliminates the need for data loading or transformation. Athena does not modify your data in Amazon S3.

> **Note:** In regions where AWS Glue is supported, Athena uses the AWS Glue Data Catalog as a central location to store and retrieve table metadata throughout an AWS account.

For this exercise we will use the zip code to city and state mapping from below S3 bucket

```
  s3://~ingestionbucket~/raw/zipcodes

```
> Note: The above dataset is listed [here](http://federalgovernmentzipcodes.us/)

The `zipcodedata.csv` file contains data in CSV format like below:

Zipcode | ZipCodeType | City	 |  State  |   LocationType  |	Lat | Long | Location | Decommisioned 
----------| ----- | -------- | ---------- | ------------- | --------- | ---------- | ------------- | ---------
705 |	STANDARD |	AIBONITO |	PR |	PRIMARY |	18.14 |	-66.26 |	NA-US-PR-AIBONITO |	FALSE
610 |	STANDARD |	ANASCO |	PR |	PRIMARY	| 18.28 |	-67.14 |	NA-US-PR-ANASCO |	FALSE
611 |	PO BOX |	ANGELES |	PR |	PRIMARY	| 18.28	| -66.79 |	NA-US-PR-ANGELES |	FALSE
612 |	STANDARD |	ARECIBO|	PR |	PRIMARY |	18.45	| -66.73 |	NA-US-PR-ARECIBO |	FALSE

### Create a table in Amazon Athena Data Catalog

> **Note:** When creating the table, you need to consider the following:

  - You must have the appropriate permissions to work with data in the Amazon S3 location. For more information, refer [Setting User and Amazon S3 Bucket Permissions](http://docs.aws.amazon.com/athena/latest/ug/access.html).
  - The data can be in a different region from the primary region where you run Athena as long as the data is not encrypted in Amazon S3. Standard inter-region data transfer rates for Amazon S3 apply in addition to standard Athena charges.
  - If the data is encrypted in Amazon S3, it must be in the same region, and the user or principal who creates the table must have the appropriate permissions to decrypt the data. For more information, refer [Configuring Encryption Options](http://docs.aws.amazon.com/athena/latest/ug/encryption.html).
  - Athena does not support different storage classes within the bucket specified by the LOCATION clause, does not support the GLACIER storage class, and does not support Requester Pays buckets. For more information, see [Storage Classes](http://docs.aws.amazon.com/AmazonS3/latest/dev/storage-class-intro.html),[Changing the Storage Class of an Object in Amazon S3](http://docs.aws.amazon.com/AmazonS3/latest/dev/ChgStoClsOfObj.html), and [Requester Pays Buckets](http://docs.aws.amazon.com/AmazonS3/latest/dev/RequesterPaysBuckets.html) in the Amazon Simple Storage Service Developer Guide.

1. From AWS Management Console, in the search text box, type **Amazon Athena**, select **Amazon Athena** service from the filtered list to open Amazon Athena console OR Open the [AWS Management Console for Athena](https://console.aws.amazon.com/athena/home).
2. Ensure `weblogs` is selected from the **Database** list and then choose **New Query**.
3. In the query pane, copy the following statement to create `zipcodesdata` table, and then choose **Run Query**:

> Replace the S3 bucket path in the script below with your S3 bucket path

```SQL
CREATE EXTERNAL TABLE IF NOT EXISTS zipcodesdata(
  zipcode string , 
  zipcodetype string , 
  city string , 
  state string , 
  locationtype string , 
  lat string , 
  long string , 
  uslocation string , 
  decommisioned string )
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.serde2.OpenCSVSerde' 
WITH SERDEPROPERTIES ( 
  'escapeChar'='\\', 
  'quoteChar'='\"', 
  'separatorChar'=',') 
STORED AS TEXTFILE
LOCATION
  's3://~ingestionbucket~/raw/zipcodes'
TBLPROPERTIES ("skip.header.line.count"="1")

```
> **Note:**

  - If you use CREATE TABLE without the EXTERNAL keyword, you will get an error as only tables with the EXTERNAL keyword can be created in Amazon Athena. We recommend that you always use the EXTERNAL keyword. When you drop a table, only the table metadata is removed and the data remains in Amazon S3.
  - You can also query data in regions other than the region where you are running Amazon Athena. Standard inter-region data transfer rates for Amazon S3 apply in addition to standard Amazon Athena charges.
  - Ensure the table you just created appears on the Catalog dashboard for the selected database.

#### Querying data from Amazon S3 using Athena and Glue Data Catalog table schemas

Now that you have created the table, you can run queries on the data set and see the results in AWS Management Console for Amazon Athena.

1. Choose **New Query**, copy the following statement into the query pane, and then choose **Run Query**.

```SQL
    SELECT * FROM "weblogs"."zipcodesdata" limit 10;
```

Results for the above query look like the following: 

zipcode | 	zipCodeType |	city |	state	| locationtype |	lat |	long |	uslocation |	decommisioned
-------- | ------------ | ---- | ------- | ---------- | ------ | ---- | -------- | --------------
00705 |	STANDARD | 	AIBONITO |	PR |	PRIMARY |	18.14 |	-66.26 |	NA-US-PR-AIBONITO |	false
00610 |	STANDARD |	ANASCO |	PR |	PRIMARY	 | 18.28 |	-67.14 |	NA-US-PR-ANASCO	| false
00611 |	PO BOX |	ANGELES	PR |	PRIMARY	| 18.28	| -66.79 |	NA-US-PR-ANGELES |	false

2. Choose **New Query**, copy the following statement into the query pane, and then choose **Run Query** to query for the number of page views per state to see which users interest in products. For this query we will join username across tables `joindatasets` and `zipcodesdata` 

```SQL
SELECT state,
        request as page,
         count(request) AS totalviews
    FROM zipcodesdata z, joindatasets  m
    WHERE z.zipcode = m.zip
    GROUP BY  state, request
    ORDER BY  state

```


# Visualization using Amazon QuickSight
In this section we will visualize the data from previous analysis in QuickSight. If you are new to Amazon QuikSight then you will have to sign up for QuickSight, refer this **[Setting Up QuikSight](https://docs.aws.amazon.com/quicksight/latest/user/setup-new-quicksight-account.html#setup-quicksight-for-existing-aws-account)** documentation to get set up to use Amazon QuickSight. If you have only one user (author or admin), you can use Amazon QuickSight for free.

Once you have signed up for QuickSight successfully next step is to grant QuickSight permissions to your AWS resources. Please refer **[Managing Amazon QuickSight Permissions to AWS Resources](https://docs.aws.amazon.com/quicksight/latest/user/managing-permissions.html)** documentation on how to grant these permissions.

> **Note:** Please ensure that you are in US East (N. Virginia) region before you execute this lab

#### Configuring Amazon QuickSight to use Amazon Athena as data source
1. From Amazon QuickSight dashboard console, Click on **Manage data** on the top-right corner of the webpage to review existing data sets.
2. Click on **New data set** on the top-left corner of the webpage and review the options.
3. Select **Athena** as a Data source.
4. On **New Athena data source** dialog box, enter **Data source name** e.g. MyAthenaDatasource
5. Click on **Validate connection** to make sure you have the permissions to access Athena.
6. Click **Create data source**. 
7. Choose `weblogs` database from **Database: contain sets of tables** dropdown, wll tables under `weblogs` should get listed. You can choose a table to visualize the data or create a custom SQL. In this lab we will create a custom SQL.
8. Click **Use custom SQL** 

 > **Note:** In QuickSight, when creating a new data set based on a direct query to a database, you can choose an existing SQL query or create a new SQL query. You can use either an existing or new query to refine the data retrieved from a database, or to combine data from multiple tables. Using a SQL query, you can specify SQL statements in addition to any join criteria to refine the data set. If you want to join tables only by specifying the join type and the fields to use to join the tables, you can use the join interface instead. For more information about using the join interface, see [Joining Tables](https://docs.aws.amazon.com/quicksight/latest/user/joining-tables.html).
 > For this lab we will use QuickSight's join interface to create custom sql

 9. On **Enter custom SQL query** dialogbox, click **Edit/Preview data** button. This should take you join interface page.
 10. On the data preparation page, on top left corner, select **Query** under **Data source** 
  
  > **Note:** SPICE is Amazon QuickSight's Super-fast, Parallel, In-memory Calculation Engine. SPICE is engineered to rapidly perform advanced calculations and serve data. By using SPICE, you save time because you don't need to retrieve the data every time you change an analysis or update a visual.

  11. On the data preparation page, expand **Schema** pane and select `weblogs` database from the drop down. This selection should populate all the tables under `weblogs` database. 
  12. Expand **Tables** pane and select tables `zipcodesdata`. This table is on the left when you are choosing a join type and join columns. The table appears in the join interface.
  > If tables are not displayed then select **Select tables** option under **Tables** pane.
  13. Select `joindatasets` from **Tables** pane.  This table is on the right when you are choosing a join type and join columns. The table appears in the join interface and a join appears between the two tables.
  14. Choose the join (2 red dots) to open the **Configure join** pane.
  15. Enter the join column information:
      - In the **Data sources** section of the **Configure join** pane, click on **Enter a field**, choose the join column, `zipcode` for the `zipcodesdata` table. 
      - Choose the join column, `zip` for the table `joindatasets`.
      > **Note:** You can select mulitple join columns by clicking **+Add a new joint clause**
  16. In the **Configure join** pane, under **Join types**, choose the **Inner** join type and click **Apply**
      - The join icon updates to indicate that the join type and columns have been selected.
      - The fields from the table to the right appear at the bottom of the **Fields** pane.
  17. On the data preparation page, from left hand pane, expand **Fields** pane and notice that QuickSight automatically identifies geospatial data types like `zipcode`, `city`, `state` and so on.
  18. Notice that QuickSight did not recognize the timestamp format by default since the logs have custom timestamp format. 
      - From **Fields** pane select `timestamp` field, select the dropdown arrow for the `timestamp` field.
      - Select **Change data type** from drop down menu
      - Select **Date** from **Type** menu
      - On **Edit date format** dialog, enter the format `dd/MMM/yyyy:HH:mm:ss` and click **Validate**. You should see that QuickSight is now able to recognize the `timestamp` as a valid **Date** type
      - Click **Update** to apply the change.  
  19. From **Fields** pane, filter the dataset to remove columns that are note required for analysis. Uncheck columns `bytes`, `firstname`, `zip`,`zipcodetype`, `http`, `uslocation`, `locationtype`,`decommisioned`
  20. (Optional) At top of the page, enter name for the dashboard E.g. MyFirstDashboard
  20. Click **Save & visualize** 
  
### Visualizing the data using Amazon QuickSight

Now that you have configured the data source and created the custom sql, in this section you will filter the data to visualize the number of users by city by state.

> **Note:** SPICE engine might take few minutes to load the data. You can start building the visualization as the data is getting loaded in background.

1. On the QuickSight dashboard page, under **Visual Types** pane, select **Points on map** visulization.
2. Expand the **Field wells** pane by clicking on dropdown arrows at top-right corner of the page under your username.
3. From **Field list** pane, drag `state` field to **Geospatial** bucket, drag `city` field to **Color** bucket and drag `username` field to **Size** bucket
4. Based on above selections QuickSight should plot the data repectively across U.S maps.
5. Click on the field name `username` in **Size** from **Field wells** to reveal a sub-menu.
5. Select **Aggregate:Count distinct** to aggregate by distinct users.
5. From the visulization to see which state has the maximum number of users for the website.

#### Add age based filter to visualize the dataset 

1. On the QuickSight dashboard page, click **+ Add** button on top-left corner
2. Select **Add visual** mennu item to add a new visual to the dashboard
3. From **Visual Types** pane, select **Horizontal bar chart** visualization.
4. Expand the **Field wells** pane by clicking on dropdown arrows at top-right corner of the page under your username.
4. From **Field list** pane, drag `age` field to **Y axis** bucket and drag `username` field to **Value** bucket.
5. Based on above selections QuickSight should plot the data repectively.
6. To add filter to `age`,
    - Select the dropdown for `age` field from the **Fields list**. 
    - Select **Add filter for this field** from the dropdown menu.
    - From **Applied Fiters**, clcik **Include - all** to open the current filters
    - From the age list select `25` and click **Apply** and then **Close**
7. To filter the data only for the age 25

#### Visualize the monhtly data for all web page request

1. On the QuickSight dashboard page, click **+ Add** button on top-left corner
2. Select **Add visual** mennu item to add a new visual to the dashboard
3. From **Visual Types** pane, select **Line chart** visualization.
4. Expand the **Field wells** pane by clicking on dropdown arrows at top-right corner of the page under your username.
5. From **Field list** pane, drag `timestamp` field to **X axis** bucket, drag `username` field to **Value** bucket and `request` to **Color** bucket
6. Based on above selections QuickSight should plot the data repectively.
6. To add filter to `request`,
    - Select the dropdown for `request` field from the **Fields list**. 
    - Select **Add filter for this field** from the dropdown menu.
    - From **Applied Fiters**, clcik **Include - all** to open the current filters
    - From the **Filter type**, select **Custom filter** and select **Conatins** filter. In the text bo under **Contains** enter `GET` and click **Apply** and then **Close**
7. Click on the field name `timestamp` in **X-axis** to reveal a sub-menu.
8. Select **Aggregate:Day** to aggregate by day.
9. Use the slider on X-axis to explore the daily request pattern for a particular month.



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


| userprofile-secure | userprofile | 
| ------------- |:-------------:| 
| Customer ID | Customer ID |
| Age | Age |
| ZIP | ZIP |
| First Name | First Name |
| Last Name | Last Name |
| SSN Hash | SSN |
| Credit Card Hash | Credit Card |

### Create a UDF to simplify apply a hash function to a columns
In order to protect sensative data, we will want to eliminate columns or hash sensitive fields. In this example we will hash user profile SSN's and credit card numbers. This will allow analysts to join profiles that share the same SSN or credit card, but encodes the sensitive data by applying a one-way hash algorith.

#### Create Glue Job

1. From AWS Management Console, in the search text box, type **AWS Glue**, select **AWS Glue** service from the filtered list to open AWS Glue console OR Open the [AWS Management Console for AWS Glue](https://console.aws.amazon.com/glue/home).
2. From **Jobs** menu page, click **Add job** button
3. Follow the instructions in the **Add job** wizard
   - Under **Job properties** step, Enter `udfjob` in the **Name** text box
   - Under **IAM role** drop down select `AWSGlueServiceRoleDefault`
   - Keep rest of the default the same and click **Next** button
   - Under **Data source** step, choose `userprofile` data catalog table and click **Next**  button
   - Under **Data target** step, choose **Create tables in your data target** option 
	 - Choose **Amazon S3** from **Data store** drop down
	 - Choose **Parquet** from **Format** drop down
	 - From **Target path** choose `~ingestionbucket~/weblogs/userprofile-secure` S3 bucket and click **Next** button
   - Under **Schema** step, keep default and click **Next** button
   - Under **Review** step, review the selections and click **Save job and edit script** button
4. Under **Edit Script** step, based on the **Add Job** wizard selection, AWS Glue creates a PySpark script which you can edit to write your logic. The AWS Glue created code coverts the source data to parquet but does not flatten the request and timestamp. Let's update the code to add our custom logic to flatten the columns.
   - Select all the code under **Edit Script** replace it with below and click **Save** button to save the changes

> Replace the S3 bucket path in the script below with your S3 bucket path


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

datasource0 = glueContext.create_dynamic_frame.from_catalog(database = "weblogs", table_name = "userprofile", transformation_ctx = "datasource0")


## @convert glue DynamicFrame to DataFrame to manipulate the columns
dataframe0 = DynamicFrame.toDF(datasource0)

hash_cc_f = udf(lambda x: hash_cc(x), StringType())

dataframe0 = dataframe0.withColumn("hash_cc", hash_cc_f(dataframe0["cc"])).withColumn("hash_ssn", hash_cc_f(dataframe0["ssn"]))
dataframe0 = dataframe0.drop('cc').drop('ssn').drop('password')

## @convert dataframe to glue DynamicFrame and write the output in parquet format
datasource1 = DynamicFrame.fromDF(dataframe0, glueContext, "name1")


datasink4 = glueContext.write_dynamic_frame.from_options(frame = datasource1, connection_type = "s3", connection_options = {"path": 's3://~ingestionbucket~/weblogs/userprofile-secure'}, format = "parquet", transformation_ctx = "datasink4")

job.commit()
```


### Create a glue crawler for the Secure Data
1. From AWS Management Console, in the search text box, type **AWS Glue**, select **AWS Glue** service from the filtered list to open AWS Glue console OR Open the [AWS Management Console for AWS Glue](https://console.aws.amazon.com/glue/home).
2. From **AWS Glue** dashboard, from left hand menu select **Crawlers** menu item
3. From **Crawlers** page, click **Add crawler** button
4. On **Crawler Info** wizard step, enter crawler name `userprofile-secure`, keep the default on the page and click **Next** button
5. On **Data Store** step, choose S3 from **Choose a data store** drop down. Choose `s3://~ingestionbucket~/weblogs/userprofile-secure` S3 bucket location from **Include path**. Keep other defaults the same and click **Next** button
6. Choose **No** and click **Next** on **Add another data store** 
7. On **IAM Role** step, choose **Choose an existing IAM role** option and select `AWSGlueServiceRoleDefault` from **IAM role** drop down. click **Next**
8. On **Schedule** step keep the default **Run on demand** option and click **Next**
9. On **Output** step, choose `weblogs` database from **Database** drop down. Keep default the same and click **Next** button
10. On **Review all steps** step, review the selections and click **Finish**. this should take to back to **Crawlers** dashboard
11. On **Crawlers** dashboard, select the crawler that you created in above steps and click **Run Crawler** button
12. The crawler will go into *Starting* to *Stopping* to *Ready* state
13. Once the crawler is in *Ready* state, from left hand menu select **Databases**
14. From **Databases** page select `weblogs` database and select **Tables in weblogs** link. You should see table `userprofile-secure` listed along with previously created tables.
15. From **Tables** page, select `userprofile-secure` table and explore the table definition that glue crawler created.


# View the Data
Now that the weblogs are available in Amazon S3, the analyics team would like access to the data. You'll use Amazon Athena to query the data using SQL Statements. This will allow you to query the data without viewing the sensitive data.

```SQL
SELECT first_name, last_name, hash_cc, hash_ssn FROM "weblogs"."userprofile_secure" limit 10;
```

## Athena Create Table as Select

The simplest way to convert a table into a more efficient format is to user the Athena Create Table as Select (CTAS) capability. It is as simple as running a query in Athena and providing the destination, file format, and partitioning information needed. Athena will add the new table to the glue data catalog, including the partition date.

1. In the Athena console, click create a new query, the + icon next to the query tab.
1. Copy and paste the following: <br/>
```SQL
CREATE TABLE IF NOT EXISTS userprofileparquet
  WITH (format='PARQUET', 
  		parquet_compression='SNAPPY', 
  		partitioned_by=ARRAY['age'], 
  		external_location='s3://~ingestionbucket~/weblogs/ctas-sample') AS
	SELECT first_name, 
		   last_name, 
		   username, 
		   email, 
		   ip_address, 
		   phone, 
		   zip,
		   age
	FROM "weblogs"."userprofile"
```
Once the query is run, you can look at the list of tables in Athena and see this table has been added, including the partitions.


#### Extra Credit - Test Role Based Access

1. Create 2 new users, one has access to s3://~ingestionbucket~/prepared/userprofile-secure, one does not.
1. Run athena query against Customer with user1 and user2
1. Run athena query against CustomerRestricted with user1 and user2

### Live Data Feed
What about the data from the Kinesis stream? That is being written to the s3://~ingestionbucket~/weblogs/live location. Now that you've used the crawler a few times, on your own create a new crawler that creates the table for the data populated by the kinesis firehose stream.

## Bonus Lab Exercise - Advanced AWS Users
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
1. Notebook S3 Path: s3://*~ingestionbucket~*/admin
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

# Clean Up

Open the Cloudformation Console and delete the workshop stack. If you leave the workshop running it will continue to generate data and incur charges.
