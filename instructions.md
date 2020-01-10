# Welcome to the AWS Serverless Data Lake Workshop

# Serverless Ingestion using Amazon Kinesis Firehose
The first step of data processing in a data lake is to land data into S3. To help with this the cloud engineering team has created three different extracts (user activity, user profile, and zip code data) from their databases. These extracts have been placed into a S3 bucket. In addition to the extracts, a Kinesis Firehose has been set up to move web logs written to CloudWatch logs into S3. Using these data sets we will explore various ways to process data within our data lake. 

## Kinesis Firehose Delivery Steam
Kinesis Firehose provides a fully managed stream processing service that's highly scalable and can deliver data to S3. The application teams publish the log files to cloudwatch logs via the cloudwatch agent. Currently, the logs are being published to the //^stackname^/apache CloudWatch Log Group.

### Lab
This section requires outputs from the CloudFormation stack output. If the CloudFormation stack has not yet completed, please wait until it has completed.

We will verify that the log files are moving from the cloudwatch logs to the S3 bucket via Kinesis Firehose.

**It may take a few minutes for data to show up in Kinesis**

>**Note:** If you are using Amazon Kinesis for the firt time then you will see the gettting started page. Click on **Get started** button to continue


1. Under Services, Type 'Kinesis'.
1. Under 'Kinesis Firehose Delivery Streams', select ^stackname^-ApacheLogsKinesis-*random id*.
1. Click the monitoring tab.
1. Here you will see the delivery stream metrics.
1. **Incoming Bytes**: The amount of data ingested by the stream.
1. **Incoming Records**: The number of records ingested by the stream .
1. **Execute Processing Duration**: The amount of time it takes to transform the data in the lambda function before it lands in S3.
1. **Execute Process Success**: The number of successful transformation calls by the stream.
1. **SucceedProcessing Records**: The number of records successfully processed.
1. **SucceedProcessing Bytes**: The amount of data successfully processed.
1. **DeliveryToS3 DataFreshness**: The age, in seconds, of the oldest record in the stream. All other data has been processed.
1. **DeliveryToS3 Success**: The number of files written to S3.
1. **DeliveryToS3 Records**: The number of records written to S3.
1. **DeliveryToS3 Bytes**: The number of bytes written to S3.
1. Click the Details Tab at the top.
1. Find the 'Amazon S3 destination' section and click the link for the S3 bucket.
1. Click 'weblogs'.
1. Drill down into today's date & time and choose a file. The files will be stored in UTC time.
1. Click 'Open' and open the file in a text editor.
1. It should contain the IP, username, timestamp, request path, and bytes downloaded.


<details><summary>Additional Details</summary>

There's a lot going on here and worth exploring. In reality, there is a lambda function generating the log data and writing it to CloudWatch logs. CloudWatch logs then has a Subscription Filter that will write any logs in the /^stackname^/apache log group to Kinesis Firehose.

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

Lastly, the logs written from CloudWatch to Kinesis are in a compressed JSON format. Not only are they harder to read in a compressed JSON format, they aren't written in a JSON compliant format. Each line is a JSON file, but there aren't commas between each line so JSON parsing fails. To correct for this a Firehose transform will execute a lambda function that decompresses the file and returns the data payload which is in a CSV format.

</details>


# Serverless Extract, Transform and Load using AWS Glue

Generally, raw data is unstructured/semi-structured and inefficient for querying. In its raw format, Apache Weblogs are difficult to query. Also, a lot of times there is a need to transform the raw datasets by either augmenting or reducing the data to derive meaningful insights.
As part of this lab we will start with creating the table definitions (schemas) from the raw datasets that we have.
Below are the datasets that we will be working with:
- `useractivity.csv`
- `zipcodedata .csv`
- `userprofile.csv`

These datasets are downloaded into the S3 bucket at:

```
 s3://^ingestionbucket^/raw/useractivity
 s3://^ingestionbucket^/raw/userprofile
 s3://^ingestionbucket^/raw/zipcodes
```

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

1. From AWS Management Console, in the search text box, type **AWS Glue**, select **AWS Glue** service from the filtered list to open AWS Glue console OR Open the <a href="https://console.aws.amazon.com/glue/home?region=us-east-1" target="_blank">AWS Management console for Amazon Glue</a>.
2. To analyze the weblogs dataset, you start with a set of data in S3. First, you will create a database for this workshop within AWS Glue. A database is a set of associated table definitions, organized into a logical group.
3. From the left hand menu of the AWS Glue console, click **Databases**
4. Click on the **Add Database** button.
5. Enter the Database name as `weblogs`. You can skip the description and location fields and click on **Create**.

### Crawl datasets to create table definitions

The first step is to crawl the datasets to create table definitions in Glue Data Catalog database `weblogs`. The table definitions will help us understand this unknown dataset; you will discover that the data is in different formats depending on the IT system that provided the data.

AWS Glue crawler will create the following tables in the `weblogs` database:
- `useractivity`
- `userprofile`

#### Steps to create crawler

1. From AWS Management Console, in the search text box, type **AWS Glue**, select **AWS Glue** service from the filtered list to open AWS Glue console OR Open the <a href="https://console.aws.amazon.com/glue/home?region=us-east-1" target="_blank">AWS Management console for Amazon Glue</a>.
2. From the **AWS Glue** dashboard, from the left hand menu select **Crawlers** menu item
3. From the **Crawlers** page, click the **Add crawler** button
4. On the **Crawler Info** wizard step, enter crawler name `rawdatacrawler`, keep the defaults on the page the same and click **Next** button
5. On the **Data Store** step, choose S3 from **Choose a data store** drop down. Enter `s3://^ingestionbucket^/raw` as S3 bucket location for **Include path**.
5. Expand the **Exclude patterns (optional)** section and enter `zipcodes/**` in **Exclude patterns** text box (We will exclude the zipcodes file in this exercise and pick it up later in the lab). Click the **Next** button
6. Choose **No** and click **Next** on **Add another data store**
7. On the **IAM Role** step, choose the **Choose an existing IAM role** option and select `^gluerole^` from **IAM role** drop down. click **Next**
8. On the **Schedule** step keep the default **Run on demand** option and click **Next**
9. On the **Output** step, choose the `weblogs` database from the **Database** drop down. Keep defaults the same and click **Next** button
10. On the **Review all steps** step, review the selections and click **Finish**. This should take you back to the **Crawlers** dashboard
11. On the **Crawlers** dashboard, select the crawler that you created in the above steps and click the **Run Crawler** button
12. The crawler will go into *Starting* to *Stopping* to *Ready* state
13. Once the crawler is in *Ready* state, from the left hand menu select **Databases**
14. From the **Databases** page select *weblogs* database and select **Tables in weblogs** link. You should see two tables `useractivity` and `userprofile` listed.
15. From the **Tables** page, select `useractivity` table and explore the table definition that glue crawler created.
16. From the **Tables** page, select `userprofile` table and explore the table definition that glue crawler created.


### Data flattening and format conversion

Once the `useractivity` and `userprofile` table definitions are created, the next step is to create a glue job. In this job we will flatten the *request* and *timestamp* columns and convert the original file format from csv to a compact, efficient format for analytics, i.e. Parquet. We will evaluate the query efficiencies in Athena based on source file formats. 

The converted table will look like this:

ip_address|username |timestamp | request|http | bytes |  requesttype|topdomain|toppage|subpage | date  | time | year | month
---- | ----| ------------ | ----------| ----| --------| ------------ | ------ | ------ | ----- | ------ | ---- | ---- | ----
105.156.115.196 |	ontistesns0 |	17/Jan/2018:10:43:54 |	GET /petstore/Cats/Treats |	200 |	    314 |   GET  |        petstore |   Cats  |  Treats | 17/Jan/2018 | 10:43:54 | 2018 | 1 
57.143.147.52 |	agkgamyaar4 |	14/Jun/2018:06:39:54 |	GET /petstore/Fish/Food	|    200	|    575  |   GET    |     petstore  |  Fish  |  Food  |  14/Jun/2018  | 06:39:54 | 2018 | 6
29.152.175.209 |	nealaoaaoc9 |	6/Jan/2018:06:51:54	 |   GET /petstore/Bird/Treats |	200	   | 419   |  GET    |     petstore |   Birds  | Treats  | 6/Jan/2018 | 06:51:54 | 2018 | 1


#### Steps to create glue job
 As part of this step you will create a glue job, update the default script and run the job. We will be using the AWS Management Console to create a SageMaker Jupyter notebook which will run the scripts on an AWS Glue Development Endpoint. Development endpoints provide the compute needed to run the Spark Job without having to wait until a cluster gets created to execute the code. This will reduce the feedback loops in the development and testing effort.

 > **Note:** For those who have not worked with Jupyter notebooks, think of them as a Integrated Development Environment (IDE). It is simply a place you can write, annotate, and execute code. Code is organized in blocks/section and each block can be executed one at a time.

1. From the AWS Management Console, in the search text box, type **AWS Glue**, select **AWS Glue** service from the filtered list to open AWS Glue console OR Open the <a href="https://console.aws.amazon.com/glue/home?region=us-east-1" target="_blank">AWS Management console for Amazon Glue</a>.
2. From the AWS Glue dashboard left hand menu select checkbox **Dev endpoints** menu item
3. From the **Dev endpoints** menu page, selct the checbox by the '^stackname^' endpoint. click **Action** button and **Create SageMaker Notebook**.
4. Follow the instructions in the **Create Notebook** screen.
   - Under the  **Notebook Name** step, Enter aws-glue-`^stackname^`
   - Under the **Attach to development endpoint** drop down select datalake-^stackname^ 
   - Select 'Choose an existing IAM Role' radio button.
   - For the IAM Role, select `^gluerole^`
   - For VPC (option), select `DataLakeVpc-^stackname^`
   - For the Subnet, select `Public-DataLakeVpc-^stackname^`
   - Select the security group that starts with '^stackname^-GlueSecurityGroup'
   - Use the defaults for KMS and click `Create Notebook`
   - Wait until the Notebook is in the 'Ready' state.
5. Select the Notebook `aws-glue-^stackname^`, and select 'Open Notebook'. Once the notebook opens, select the `New` button and choose `Terminal`. Now copy the sample notebook from your bucket into the notebook by entering the following command into the terminal window
```
aws s3 cp s3://^ingestionbucket^/instructions/labs.ipynb SageMaker/labs.ipynb
```
5. Click the Jupyter icon in the upper left to return the main menu.
6. Now you should see **labs.ipynb** in the list. Click it to open and follow the instructions. 
7. Select each code block under the **Initialization** heading and click the **Run** button to run the code in each code block. **Please wait for the 1st section to complete before running the second section.**
8. Next select the code block under the **Lab - Transform / Decode data with AWS Glue** heading and click the **Run** button. This code creates a Glue job to split apart and transform some of the data elements.
9.  Once the job is succeeded, go to S3 console and browse to `s3://^ingestionbucket^/weblogs/useractivityconverted` S3 bucket
10. Under the `useractivityconverted` S3 folder you should see Parquet files created by the job, partitioned by `toppage` column.

#### Explore the new dataset that we created in the previous step

1. From the AWS Management Console, in the search text box, type **AWS Glue**, select the **AWS Glue** service from the filtered list to open AWS Glue console OR Open the <a href="https://console.aws.amazon.com/glue/home?region=us-east-1" target="_blank">AWS Management console for Amazon Glue</a>.
2. From the **AWS Glue** dashboard, from the left-hand menu select **Crawlers** menu item
3. From the **Crawlers** page, click **Add crawler** button
4. On the **Crawler Info** wizard step, enter crawler name `useractivityconvertedcrawler`, keep the default on the page and click **Next** button
5. On the **Data Store** step, choose S3 from **Choose a data store** drop down. Enter `s3://^ingestionbucket^/weblogs/useractivityconverted` as S3 bucket location for **Include path**. Keep other defaults the same and click **Next** button
6. Choose **No** and click **Next** on **Add another data store** 
7. On the **IAM Role** step, choose **Choose an existing IAM role** option and select `^gluerole^` from **IAM role** drop down. Click **Next**
8. On the **Schedule** step keep the default **Run on demand** option and click **Next**
9. On the **Output** step, choose `weblogs` database from the **Database** drop down. Keep defaults the same and click **Next** button
10. On the **Review all steps** step, review the selections and click **Finish**. This should take you back to the **Crawlers** dashboard
11. On **Crawlers** dashboard, select the crawler that you created in above steps and click **Run Crawler** button
12. The crawler status should change from *Starting* to *Stopping* to *Ready* state
13. Once the crawler is in the *Ready* state, from the left hand menu select **Databases**
14. From the **Databases** page select `weblogs` database and select **Tables in weblogs** link. You should see 3 tables `useractivity`, `userprofile` and `useractivityconverted` listed.
15. From the `Tables` page, select `useractivityconverted` table and explore the table definition that glue crawler created.

	
# Serverless Analysis of data in Amazon S3 using Amazon Athena

> If you are using Amazon Athena for the first time, follow the <a href="https://docs.aws.amazon.com/athena/latest/ug/setting-up.html" target="_blank">Setting Up Amazon Athena</a> to make sure you have the correct permissions to execute the lab. Refer section Attach Managed Policies for Using Athena.

> In this workshop we will leverage the AWS Glue Data Catalog `weblogs` for serverless analysis in Amazon Athena. If you are new to Athena you can leverage AWS Glue Data Catalog, but if you had previously created databases and tables using Athena or Amazon Redshift Spectrum but not upgraded Athena to use AWS Glue Data Catalog, then please follow the steps in [Upgrading to the AWS Glue Data Catalog Step-by-Step](https://docs.aws.amazon.com/athena/latest/ug/glue-upgrade.html) documentation before proceeding further.

Athena integrates with the AWS Glue Data Catalog, which offers a persistent metadata store for your data in Amazon S3. This allows you to create tables and query data in Athena based on a central metadata store available throughout your AWS account and integrated with the ETL and data discovery features of AWS Glue.


> **Note:** In regions where AWS Glue is supported, Athena uses the AWS Glue Data Catalog as a central location to store and retrieve table metadata throughout an AWS account.

### Explore AWS Glue Data Catalog in Amazon Athena
1. From the AWS Management Console, in the search text box, type **Amazon Athena**, select **Amazon Athena** service from the filtered list to open Amazon Athena console OR Open the <a href="https://console.aws.amazon.com/athena/home" target="_blank">AWS Management Console for Athena</a>.
2. If this is your first time visiting the AWS Management Console for Athena, you will get a Getting Started page. Choose **Get Started** to open the Query Editor. If this isn't your first time, the Athena Query Editor opens.
3. Make a note of the AWS region name, for example, for this lab you will need to choose the **US East (N. Virginia)** region.
4. In the **Athena Query Editor**, you will see a query pane with an example query. Now you can start entering your query in the query pane.
5. On left hand side of the screen, under **Database** drop down select `weblogs` database if not already selected. After selecting `weblogs` you should see tables `useractivity`, `userprofile` and `useractivityconverted` listed.

### Querying data from Amazon S3
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

By partitioning your data, you can restrict the amount of data scanned by each query, thus improving performance and reducing cost. Athena leverages Hive for partitioning data. You can partition your data by any key. A common practice is to partition the data based on time, often leading to a multi-level partitioning scheme. For our weblogs data you will partition it by `request` as we want to understand the number of hits a user makes for a given `toppage`

1. Choose **New Query*** or **+**, copy the following statement into the query pane, and then choose **Run Query** to get the total number of hits for Dog products

```SQL
SELECT count(*) as TotalCount FROM "weblogs"."useractivityconverted" where toppage = 'Dogs';

```
Results for the above query look like the following: 

  | TotalCount |
 | ------   |
  |	2064987 |

> **Note:** This query executes much faster because the data set is partitioned and it is in an optimal format - Apache Parquet (an open source columnar). The amount of data scanned is 0KB and it takes ~1.5 seconds to execute. Athena charges you by the amount of data scanned per query. You can save on costs and get better performance if you partition the data, compress data, or convert it to columnar formats such as Apache Parquet.

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

> **Note:** This query executes on partitioned Parquet format data, the amount of data scanned is only ~750KB and it takes ~2.6 seconds to execute. Athena charges you by the amount of data scanned per query. You can save on costs and get better performance if you partition the data, compress data, or convert it to columnar formats such as Apache Parquet.

# Join and relationalize data with AWS Glue

In previous sections we looked at how to work with semi-structured datasets to make them easily queryable and consumable. In the real world, hardly anyone works with just one dataset. Normally you would end up working with multiple datasets from various datasources having different schemas. 

In this exercise we will see how you can leverage AWS Glue to join different datasets to load, transform, and rewrite data in AWS S3 so that it can easily and efficiently be queried and analyzed.
You will work with `useractivity` and `userprofile` datasets, the table definitions for which were created in the previous section.

### Create AWS Glue job 

 > Return to the SageMaker notebook.

1. If you closed the jupyter notebook, follow the steps 1-3 to reopen the notebook. From AWS Management Console, in the search text box, type **AWS Glue**, select **AWS Glue** service from the filtered list to open AWS Glue console OR Open the <a href="https://console.aws.amazon.com/glue/home" target="_blank">AWS Management Console for AWS Glue</a>.
2. From the **Notebook Servers** menu page, Select the `aws-glue-^stackname^` notebook and click **Open Notebook** button
3. Open the labs workbook
4. Find the section **Lab - Join and relationalize data with AWS Glue**
5. Let's update the code to add our custom logic to flatten the columns.

5. Select the **Run ** button to execute the glue job, 
6. On the **Parameters (optional)** dialog, keep the default and click **Run job** button
10. Once the job is succeeded, go to S3 console and browse to `s3://^ingestionbucket^/weblogs/joindatasets` S3 bucket
11. Under the `joindatasets` S3 folder you should see Parquet files created by the job

#### Explore the new dataset created in the previous step 

1. From the AWS Management Console, in the search text box, type **AWS Glue**, select **AWS Glue** service from the filtered list to open AWS Glue console OR Open the <a href="https://console.aws.amazon.com/glue/home" blank="_blank">AWS Management Console for AWS Glue</a>.
2. From the **AWS Glue** dashboard, from the left hand menu select **Crawlers** menu item
3. From the **Crawlers** page, click **Add crawler** button
4. On the **Crawler Info** wizard step, enter crawler name `joindatasetscrawler`, keep the default on the page and click **Next** button
5. On the **Data Store** step, choose S3 from **Choose a data store** drop down. Choose `s3://^ingestionbucket^/weblogs/joindatasets` S3 bucket location from **Include path**. Keep other defaults the same and click **Next** button
6. Choose **No** and click **Next** on **Add another data store** 
7. On the **IAM Role** step, choose **Choose an existing IAM role** option and select `^gluerole^` from **IAM role** drop down. click **Next**
8. On **Schedule** step keep the default **Run on demand** option and click **Next**
9. On **Output** step, choose `weblogs` database from **Database** drop down. Keep default the same and click **Next** button
10. On the **Review all steps** step, review the selections and click **Finish**. This should take you back to the **Crawlers** dashboard
11. On the **Crawlers** dashboard, select the crawler that you created in the above steps and click **Run Crawler** button
12. The crawler will go into *Starting* to *Stopping* to *Ready* state
13. Once the crawler is in *Ready* state, from the left hand menu select **Databases**
14. From the **Databases** page select `weblogs` database and select **Tables in weblogs** link. You should see table `joindatasets` listed along with previously created tables.
15. From the **Tables** page, select `joindatasets` table and explore the table definition that glue crawler created.

# Serverless Analysis of data in Amazon S3 using Amazon Athena Contd.
In previous sections we saw how Athena can leverage the AWS Glue Data Catalog. In this section we will explore how you can create a new table schema in Athena but still use the same AWS Glue Data Catalog. When you create a new table schema in Athena, Athena stores the schema in a data catalog and uses it when you run queries. Athena uses an approach known as schema-on-read, which means a schema is projected on to your data at the time you execute a query. This eliminates the need for data loading or transformation. Athena does not modify your data in Amazon S3.

> **Note:** In regions where AWS Glue is supported, Athena uses the AWS Glue Data Catalog as a central location to store and retrieve table metadata throughout an AWS account.

For this exercise we will use the zip code to city and state mapping from the below S3 bucket

```
  s3://^ingestionbucket^/raw/zipcodes

```
> Note: The above dataset is listed <a href="http://federalgovernmentzipcodes.us/" target="_blank">here</a>

The `zipcodedata.csv` file contains data in CSV format like below:

Zipcode | ZipCodeType | City	 |  State  |   LocationType  |	Lat | Long | Location | Decommisioned 
----------| ----- | -------- | ---------- | ------------- | --------- | ---------- | ------------- | ---------
705 |	STANDARD |	AIBONITO |	PR |	PRIMARY |	18.14 |	-66.26 |	NA-US-PR-AIBONITO |	FALSE
610 |	STANDARD |	ANASCO |	PR |	PRIMARY	| 18.28 |	-67.14 |	NA-US-PR-ANASCO |	FALSE
611 |	PO BOX |	ANGELES |	PR |	PRIMARY	| 18.28	| -66.79 |	NA-US-PR-ANGELES |	FALSE
612 |	STANDARD |	ARECIBO|	PR |	PRIMARY |	18.45	| -66.73 |	NA-US-PR-ARECIBO |	FALSE

### Create a table in Amazon Athena Data Catalog

> **Note:** When creating the table, you need to consider the following:

  - You must have the appropriate permissions to work with data in the Amazon S3 location. For more information, refer to [Setting User and Amazon S3 Bucket Permissions](http://docs.aws.amazon.com/athena/latest/ug/access.html).
  - The data can be in a different region from the primary region where you run Athena as long as the data is not encrypted in Amazon S3. Standard inter-region data transfer rates for Amazon S3 apply in addition to standard Athena charges.
  - If the data is encrypted in Amazon S3, it must be in the same region, and the user or principal who creates the table must have the appropriate permissions to decrypt the data. For more information, refer to [Configuring Encryption Options](http://docs.aws.amazon.com/athena/latest/ug/encryption.html).
  - Athena does not support different storage classes within the bucket specified by the LOCATION clause, does not support the GLACIER storage class, and does not support Requester Pays buckets. For more information, see [Storage Classes](http://docs.aws.amazon.com/AmazonS3/latest/dev/storage-class-intro.html), [Changing the Storage Class of an Object in Amazon S3](http://docs.aws.amazon.com/AmazonS3/latest/dev/ChgStoClsOfObj.html), and [Requester Pays Buckets](http://docs.aws.amazon.com/AmazonS3/latest/dev/RequesterPaysBuckets.html) in the Amazon Simple Storage Service Developer Guide.

1. From the AWS Management Console, in the search text box, type **Amazon Athena**, select **Amazon Athena** service from the filtered list to open Amazon Athena console OR Open the [AWS Management Console for Athena](https://console.aws.amazon.com/athena/home).
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
  's3://^ingestionbucket^/raw/zipcodes'
TBLPROPERTIES ("skip.header.line.count"="1")

```
> **Note:**

  - If you use CREATE TABLE without the EXTERNAL keyword, you will get an error as only tables with the EXTERNAL keyword can be created in Amazon Athena. We recommend that you always use the EXTERNAL keyword. When you drop a table, only the table metadata is removed and the data remains in Amazon S3.
  - You can also query data in regions other than the region where you are running Amazon Athena. Standard inter-region data transfer rates for Amazon S3 apply in addition to standard Amazon Athena charges.
  - Ensure the table you just created appears on the Catalog dashboard for the selected database.

#### Querying data from Amazon S3 using Athena and Glue Data Catalog table schemas

Now that you have created the table, you can run queries on the data set and see the results in the AWS Management Console for Amazon Athena.

1. Choose **New Query**, copy the following statement into the query pane, and then choose **Run Query**.

```SQL
    SELECT * FROM "weblogs"."zipcodesdata" limit 10;
```

Results for the above query look like the following: 

zipcode | 	zipCodeType |	city |	state	| locationtype |	lat |	long |	uslocation |	decommisioned
-------- | ------------ | ---- | ------- | ---------- | ------ | ---- | -------- | --------------
00705 |	STANDARD | 	AIBONITO |	PR |	PRIMARY |	18.14 |	-66.26 |	NA-US-PR-AIBONITO |	false
00610 |	STANDARD |	ANASCO |	PR |	PRIMARY	 | 18.28 |	-67.14 |	NA-US-PR-ANASCO	| false
00611 |	PO BOX |	ANGELES |	PR |	PRIMARY	| 18.28	| -66.79 |	NA-US-PR-ANGELES |	false

2. Choose **New Query**, copy the following statement into the query pane, and then choose **Run Query** to query for the number of page views per state to see which users are interested in products. For this query we will join username across tables `joindatasets` and `zipcodesdata` 

```SQL
SELECT state,
        request as page,
         count(request) AS totalviews
    FROM zipcodesdata z, joindatasets  m
    WHERE z.zipcode = m.zip
    GROUP BY  state, request
    ORDER BY  state

```


# Data Visualization using Amazon QuickSight
In this section we will visualize the data from the previous analysis in QuickSight. If you are new to Amazon QuickSight then you will have to sign up for QuickSight, refer to this **[Setting Up QuickSight](https://docs.aws.amazon.com/quicksight/latest/user/setup-new-quicksight-account.html#setup-quicksight-for-existing-aws-account)** documentation to get set up to use Amazon QuickSight. If you have only one user (author or admin), you can use Amazon QuickSight for free.

Once you have signed up for QuickSight successfully, the next step is to grant QuickSight permissions to your AWS resources. Please refer to **[Managing Amazon QuickSight Permissions to AWS Resources](https://docs.aws.amazon.com/quicksight/latest/user/managing-permissions.html)** documentation on how to grant these permissions.

#### Configuring Amazon QuickSight to use Amazon Athena as data source
1. From the Amazon QuickSight dashboard console, Click on **Manage data** on the top-right corner of the webpage to review existing data sets.
2. Click on **New data set** on the top-left corner of the webpage and review the options.
3. Select **Athena** as a Data source.
4. On the **New Athena data source** dialog box, enter **Data source name** `weblogs-athena-datasource`
5. Click on **Validate connection** to make sure you have the permissions to access Athena.
6. Click **Create data source**. 
7. Choose `weblogs` database from **Database: contain sets of tables** dropdown, all tables under `weblogs` should get listed. You can choose a table to visualize the data or create a custom SQL. In this lab we will select a table.
8. Select 'zipcodesdata'
9. Click **Edit/Preview data** 
10. The Data visualizer will appear showing the zipcodes data table.
 > **Note:** In QuickSight, when creating a new data set based on a direct query to a database, you can choose an existing SQL query or create a new SQL query. You can use either an existing or new query to refine the data retrieved from a database, or to combine data from multiple tables. Using a SQL query, you can specify SQL statements in addition to any join criteria to refine the data set. If you want to join tables only by specifying the join type and the fields to use to join the tables, you can use the join interface instead. For more information about using the join interface, see [Joining Tables](https://docs.aws.amazon.com/quicksight/latest/user/joining-tables.html).
  
  > **Note:** SPICE is Amazon QuickSight's Super-fast, Parallel, In-memory Calculation Engine. SPICE is engineered to rapidly perform advanced calculations and serve data. By using SPICE, you save time because you don't need to retrieve the data every time you change an analysis or update a visual.

  11. Click the **Add Data** link above the zipcodesdata. 
  13. Select `joindatasets` from the **Tables** list and click **select** The table appears in the join interface and a join appears between the two tables.
  14. Choose the join (2 red dots) to open the **Configure join** pane.
  15. Enter the join column information:
      - In the **Data sources** section of the **Configure join** pane, click on **Enter a field**, choose the join column, `zipcode` for the `zipcodesdata` table. 
      - Choose the join column, `zip` for the table `joindatasets`.
      > **Note:** You can select multiple join columns by clicking **+Add a new joint clause**
  16. In the **Configure join** pane, under **Join types**, choose the **Inner** join type and click **Apply**
      - The join icon updates to indicate that the join type and columns have been selected.
      - The fields from the table to the right appear at the bottom of the **Fields** pane.
  17. On the data preparation page, from the left hand pane, expand the **Fields** pane and notice that QuickSight automatically identifies geospatial data types like `zipcode`, `city`, `state` and so on.
  18. Notice that QuickSight did not recognize the timestamp format by default since the logs have custom timestamp format. 
      - From the **Fields** pane select the `timestamp` field, select the dropdown arrow for the `timestamp` field.
      - Select **Change data type** from the drop down menu
      - Select **Date** from the **Type** menu
      - On the **Edit date format** dialog, enter the format `dd/MMM/yyyy:HH:mm:ss` and click **Validate**. You should see that QuickSight is now able to recognize the `timestamp` as a valid **Date** type
      - Click **Update** to apply the change.  
  19. From the **Fields** pane, filter the dataset to remove columns that are note required for analysis. Uncheck columns `bytes`, `firstname`, `zip`, `zipcodetype`, `http`, `uslocation`, `locationtype`,`decommissioned`
  20. (Optional) At the top of the page, enter name for the dashboard `weblogs-insights`
  20. Click **Save & visualize** 
  
### Visualizing the data using Amazon QuickSight

Now that you have configured the data source and created the custom sql, in this section you will filter the data to visualize the number of users by city and state.

> **Note:** SPICE engine might take few minutes to load the data. You can start building the visualization as the data is getting loaded in the background.

1. On the QuickSight dashboard page, under the **Visual Types** pane, select **Points on map** visualization.
2. Expand the **Field wells** pane by clicking on the dropdown arrows at the top-right corner of the page under your username.
3. From the **Field list** pane, drag the `state` field to the **Geospatial** bucket, drag the `city` field to the **Color** bucket and drag the `username` field to **Size** bucket
4. Based on the above selections QuickSight should plot the data respectively across U.S maps.
5. Click on the field name `username` in **Size** from **Field wells** to reveal a sub-menu.
5. Select **Aggregate:Count distinct** to aggregate by distinct users.
5. From the visualization you can see which state has the maximum number of users for the website.

#### Add age based filter to visualize the dataset 

1. On the QuickSight dashboard page, click **+ Add** button on top-left corner
2. Select the **Add visual** menu item to add a new visual to the dashboard
3. From the **Visual Types** pane, select the **Horizontal bar chart** visualization.
4. Expand the **Field wells** pane by clicking on the dropdown arrows at the top-right corner of the page under your username.
4. From **Field list** pane, drag `age` field to **Y axis** bucket and drag `username` field to **Value** bucket.
5. Based on the above selections QuickSight should plot the data respectively.
6. To add filter to `age`,
    - Select the dropdown for the `age` field from the **Fields list**. 
    - Select **Add filter for this field** from the dropdown menu.
    - From **Applied Fiters**, click **Include - all** to open the current filters. If you get alert message "We can't deterimine how many unique values are in this column....", click **Retrieve** to continue.
    - From the age list select `25` and click **Apply** and then **Close**
7. This will filter the data only for the age 25 group

#### Visualize the monthly data for all web page request

1. On the QuickSight dashboard page, click **+ Add** button on top-left corner
2. Select **Add visual** menu item to add a new visual to the dashboard
3. From the **Visual Types** pane, select **Line chart** visualization.
4. Expand the **Field wells** pane by clicking on the dropdown arrows at the top-right corner of the page under your username.
5. From the **Field list** pane, drag the `timestamp` field to the **X axis** bucket, drag the `username` field to the **Value** bucket and `request` to the **Color** bucket
6. Based on the above selections QuickSight should plot the data respectively.
6. To add a filter to the `request`,
    - Select the dropdown for `request` field from the **Fields list**. 
    - Select **Add filter for this field** from the dropdown menu.
    - From **Applied Filters**, click **Include - all** to open the current filters
    - From the **Filter type**, select **Custom filter** and select **Contains** filter. In the text under **Contains** enter `GET` and click **Apply** and then **Close**
7. Click on the field name `timestamp` in **X-axis** to reveal a sub-menu.
8. Select **Aggregate:Day** to aggregate by day.
9. Use the slider on the X-axis to explore the daily request pattern for a particular month.



# Data Governance using AWS Glue
Most large organizations will have different data classification tiers and a number of roles that have access to different classifications of data. With an S3 data lake, there are several ways to protect the data and grant access to the data.

The first layer will be to use IAM policies to grant access to IAM principles to the data in the S3 bucket. This is done with S3 bucket policies and IAM policies attached to IAM users, groups, and roles.

This approach is required if the consumer of the data requires direct access to the files or queries through Amazon Athena.

The second approach is to protect the data at the serving layer, which may be through an EMR cluster or Redshift cluster. With EMR, the cluster can authenticate users using Kerberos and Redshift can be authenticated using Redshift users or IAM credentials.

Finally, the Business Intelligence (BI) tier can authenticate users and limit visibility to reports and dashboards based on the user's group membership.

## Lab Exercise
It is common to have multiple classifications of data in the same table. One column will be more restricted than another. Because authorization in S3 is at the file level, you will need to separate out the restricted data from the less restricted data.


One solution to this problem creates two tables: one contains just the less sensitive data and other contains the full dataset. In the less sensitive dataset, we have the customer id, age, and a hash of the social security number. This will allow the Ecommerce analytics team to run demographic analytics on the profiles and aggregate profiles of the same person via the hashed SSN.

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

### Create a UDF to simplify apply a hash function to columns
In order to protect sensitive data, we will want to eliminate columns or hash sensitive fields. In this example we will hash user profile SSN's and credit card numbers. This will allow analysts to join profiles that share the same SSN or credit card, but encodes the sensitive data by applying a one-way hash algorithm.

#### Create Glue Job

1. If you closed the jupyter notebook, follow the steps 1-3 to reopen the notebook. From AWS Management Console, in the search text box, type **AWS Glue**, select **AWS Glue** service from the filtered list to open AWS Glue console OR Open the <a href="https://console.aws.amazon.com/glue/home" target="_blank">AWS Management Console for AWS Glue</a>.
2. From the **Notebook Servers** menu page, Select the `aws-glue-^stackname^` notebook and click **Open Notebook** button
3. Open the labs workbook
4. Find the section **Create a UDF to simplify apply a hash function to columns**
5. Run the section



### Create a glue crawler for the Secure Data
1. From the AWS Management Console, in the search text box, type **AWS Glue**, select **AWS Glue** service from the filtered list to open the AWS Glue console OR Open the [AWS Management Console for AWS Glue](https://console.aws.amazon.com/glue/home).
2. From the **AWS Glue** dashboard, from the left hand menu select **Crawlers** menu item
3. From the **Crawlers** page, click **Add crawler** button
4. On the **Crawler Info** wizard step, enter crawler name `userprofile-secure`, keep the default on the page and click **Next** button
5. On the **Data Store** step, choose S3 from **Choose a data store** drop down. Choose `s3://^ingestionbucket^/weblogs/userprofile-secure` S3 bucket location from **Include path**. Keep other defaults the same and click **Next** button
6. Choose **No** and click **Next** on **Add another data store** 
7. On the **IAM Role** step, choose **Choose an existing IAM role** option and select `^gluerole^` from **IAM role** drop down. click **Next**
8. On the **Schedule** step keep the default **Run on demand** option and click **Next**
9. On the **Output** step, choose `weblogs` database from **Database** drop down. Keep default the same and click **Next** button
10. On the **Review all steps** step, review the selections and click **Finish**. this should take to back to **Crawlers** dashboard
11. On the **Crawlers** dashboard, select the crawler that you created in above steps and click **Run Crawler** button
12. The crawler will go into *Starting* to *Stopping* to *Ready* state
13. Once the the crawler is in *Ready* state, from the left hand menu select **Databases**
14. From the **Databases** page select `weblogs` database and select **Tables in weblogs** link. You should see table `userprofile-secure` listed along with previously created tables.
15. From the **Tables** page, select `userprofile-secure` table and explore the table definition that glue crawler created.


# View the Data
Now that the weblogs are available in Amazon S3, the analytics team would like access to the data. You'll use Amazon Athena to query the data using SQL Statements. This will allow you to query the data without viewing the sensitive data.

```SQL
SELECT first_name, last_name, hash_cc, hash_ssn FROM "weblogs"."userprofile_secure" limit 10;
```

## Athena Create Table as Select

The simplest way to convert a table into a more efficient format is to use the Athena Create Table as Select (CTAS) capability. It is as simple as running a query in Athena and providing the destination, file format, and partitioning information needed. Athena will add the new table to the glue data catalog, including the partition date.

1. In the Athena console, click create a new query, the + icon next to the query tab.
1. Copy and paste the following: <br/>
```SQL
CREATE TABLE IF NOT EXISTS userprofileParquet
  WITH (format='PARQUET', 
  		parquet_compression='SNAPPY', 
  		partitioned_by=ARRAY['age'], 
  		external_location='s3://^ingestionbucket^/weblogs/ctas-sample') AS
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


### Make your own jobs

#### Geocode IPs

1. If you closed the jupyter notebook, follow the steps 1-3 to reopen the notebook. From AWS Management Console, in the search text box, type **AWS Glue**, select **AWS Glue** service from the filtered list to open AWS Glue console OR Open the <a href="https://console.aws.amazon.com/glue/home" target="_blank">AWS Management Console for AWS Glue</a>.
2. From the **Notebook Servers** menu page, Select the `aws-glue-^stackname^` notebook and click **Open Notebook** button
3. Open the labs workbook **Exercise 4 - Lookup**

#### Hash First & Last Name

1. Create a transformation that shows the user profile with a hashed version of the username and password.


#### Extra Credit - Test Role Based Access

1. Create 2 new users, one has access to `s3://^ingestionbucket^/prepared/userprofile-secure`, one does not.
1. Run Athena query against Customer with user1 and user2
1. Run Athena query against CustomerRestricted with user1 and user2

### Live Data Feed
What about the data from the Kinesis stream? That is being written to the `s3://^ingestionbucket^/weblogs/live` location. Now that you've used the crawler a few times, on your own create a new crawler that creates the table for the data populated by the kinesis firehose stream.

# Advanced AWS Users
The following sections are for more advanced AWS users. These labs will create EC2 instance and require users to create an SSH connection into the instances to complete the configuration.

## Bonus Lab Exercise #1 - Configure Zeppelin Notebook Server

The workshop provided the code needed to make the Glue jobs function properly. But how do you write and debug the code? A notebook server makes the development of the glue scripts simpler to test and debug by giving a user interface and immediate feedback on the results of a script. <a href="https://docs.aws.amazon.com/glue/latest/dg/dev-endpoint.html" target="_blank">Click here</a> for more information on notebooks and glue development endpoints.

#### Prerequisites
1. An AWS Keypair Generated in your account
1. A copy of the key downloaded to your computer. <a href="https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html" target="_blank"> More info</a>
1. SSH Client. 
  * Mac or Windows 10: Open a terminal window and type <code>ssh -i keypair.pem ec2-user@hostname</code>
    * If you get a permission denied error, make sure you set the permissions of the file using <code>chmod 400 keyfile.pem</code>
  * Pre-windows 10: 
    * Install PuTTY: <a href="https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/putty.html" target="_blank">More Info</a>
    * You will need to convert the pem file to a ppk file using the puttygen utility.
1. Create an AWS Glue development endpoint. Refer to the instuctions <a href="https://docs.aws.amazon.com/glue/latest/dg/console-development-endpoint.html" target="_black">here</a>.

### Lab Activities

Go to the Glue Console and Select the Glue Development Endpoint created in the prerequisites section above.
1. Select Action->Create Zeppelin Notebook Server
1. Go through the Zeppelin Notebook Wizard
1. CloudFormation stack name: aws-glue-^stackname^
1. Select the role for this notebook server: ^stackname^-notebook-role
1. KeyPair: Select the key pair from the prequisites
1. Attach a Public IP (True)
1. Notebook Username: Admin
1. Notebook S3 Path: s3://*^ingestionbucket^*/admin
1. Subnet: Pick a public subnet. Not sure which subnet is public? <a href="https://console.aws.amazon.com/vpc/home?region=us-east-1#subnets:sort=SubnetId" target="_blank">Subnet Console<a> Look at the Route Table tab of the subnet and see if the route to 0.0.0.0/0 starts with igw.
1. Click Finish. This will kick off a cloud formation script that builds out the notebook server.
1. After the notebook server is created, its status changes to CREATE_COMPLETE in the CloudFormation console. Look under the `Resources` section and click the link by the 'Zeppelin Instance' resource.
1. Copy the Public DNS entry for the instance
1. Use your SSH client and connect to the instance. <code>ssh -i keyfile.pem ec2-user@paste-hostname-here</code>
1. From the home directory, run <code>./setup_notebook_server.py</code> **include the ./ to start the script** in the terminal window. AWS Glue created and placed this script on the Amazon EC2 instance. The script performs the following actions:
  * **Type the password required to access your Zeppelin notebook**: Supply a password. You will need this password to open your Zeppelin server!
  * **Do you want a SSH key pair to be generated on the instance? WARNING this will replace any existing public key on the DevEndpoint**: Yes. Generates SSH public and private keys: The script overwrites any existing SSH public key on the development endpoint that is associated with the notebook server. As a result, any other notebook servers, Read–Eval–Print Loops (REPLs), or IDEs that connect to this development endpoint can no longer connect.
  * **Do you have a JKS keystore to encrypt HTTPS requests? If not, a self-signed certificate will be generated.**: No. This will create a self-signed certificate. You will need to put an exception in your browser to load the page.
1. Return to the Glue Console and click Notebooks or  <a href="https://console.aws.amazon.com/glue/home?region=us-east-1#etl:tab=notebooks" target="_blank">Click Here</a>
1. Click 'Zeppelin Notebook servers' tab.
1. Select your notebook server, under action select 'Open'
1. You will get an error due to a self-signed SSL certificate. This is expected. Depending on the browser, you will have to allow the exception.
1. In the upper right, click Login. User is 'admin' and password was supplied when configuring the notebook server.
1. Now you can run your scripts that you created in the prior sections in the notebook. It provides a development environment to explore the data and create the ETL transformations.

## Bonus Lab #2: Create Amazon Redshift Cluster
This lab will show to take advantage of Redshift Spectrum to add external data to your Redshift Data Warehouse.

## Create Amazon Redshift Cluster

In this task, you will create an Amazon Redshift cluster. You will need a SQL client such as SQLWorkbenchJ to connect to the Redshift cluster.

**Make sure to delete the Redshift cluster after you complete the lab.**

1. Open the AWS Console home page. Type 'Redshift' in the search box and load the Redshift console.
1. Click **Quick Launch** to launch a cluster
   - Type Type: `ds2.xlarge`
   - Number of Compute Nodes: `1`
   - Cluster Identifier: `serverless-datalake`
   - Master user name: `awsuser`
   - Master user password: *create your own password*
   - Confirm password: *re-enter password*
   - Database Port: `5439`
   - Available IAM Roles: `^stackname^-Redshift`
1. Go to the details for the newly created cluster.
1. After the cluster is in the `ready` state, search for the **JDBC URL** and copy it onto your clipboard.
1. Using the **JDBC URL**, connect to your SQL Client. For more information, <a href="https://docs.aws.amazon.com/Redshift/latest/mgmt/connecting-using-workbench.html" target="_blank">Connect Redshift to SqlWorkbenchJ</a>


### Create an External Table

In this task, you will create an external table. Unlike a normal Redshift table, an external table references data stored in Amazon S3

You will start by defining an external schema. The external schema references a database in the external data catalog and provides the IAM role identifier (ARN) that authorizes your cluster to access Amazon S3 on your behalf

1. Run this command in your SQL client, replacing INSERT-YOUR-REDSHIFT-ROLE with the RedshiftRole value from the CloudFormation (Output of the key "RedshiftRole")

```SQL
  DROP  SCHEMA IF EXISTS weblogs;

  CREATE EXTERNAL SCHEMA weblogs
  FROM DATA CATALOG
  DATABASE 'weblogs'
  IAM_ROLE 'INSERT-YOUR-REDSHIFT-ROLE' 
  CREATE EXTERNAL DATABASE IF NOT EXISTS;

```
            

> **Note:**  If you receive a message that Schema "spectrum" already exists, continue with the next step. You will now create an external table that will be stored in the spectrum schema

* Run this command in your SQL client to run a query against an external table:

```SQL
SELECT count(*) as TotalCount FROM "weblogs"."useractivity" where request like '%Dogs%';
```

This should return a result that indicates the number of rows with dogs in the request.

### Part 3: Join a Redshift table to an External Table

The true benefit of using external data is that it can be joined with data in Redshift itself. This hybrid approach allows you to store frequently queried data in Redshift in a schema optimized for the most common queries and join the data stored in your data lake. 

* Run this command to create a table in Redshift that pulls in the useractivity from the external table stored in S3.

```SQL
CREATE SCHEMA IF NOT EXISTS local_weblogs ;
drop table if exists local_weblogs.useractivity;
create table local_weblogs.useractivity
DISTSTYLE KEY
DISTKEY (username) 
SORTKEY(timestamp)
AS SELECT * FROM "weblogs"."useractivity";
```

This will create a new table that is stored in Redshift based on the useractivity data stored in S3.

* The DISTSTYLE KEY DISTKEY(username) indicates that data will be distributed to the slice based on the username column. This is useful because any aggregation queries against the username column will be on the same slice.
* The SORTKEY(timestamp) tells Redshift to save the data sorted by the timestamp.


Execute the following query to aggregate data against the useractivity table
```SQL
SELECT username, COUNT(timestamp) 
FROM local_weblogs.useractivity
GROUP BY username;
```

And compare the results to the following query:
```SQL
SELECT username, COUNT(timestamp) 
FROM weblogs.useractivity
GROUP BY username;
```

One is hitting the data local to Redshift and the other is using an external source. Keep in mind this cluster only has 1 node and Redshift is designed to be a parallel data warehouse with many nodes in the cluster.

Now, we'll show an example of joining data from your Redshift database and the external data in S3. Here we will pull in the first and last names from the user profile into the useractivity query.

```SQL
SELECT ua.username, first_name, last_name, COUNT(timestamp) 
FROM local_weblogs.useractivity ua
INNER JOIN weblogs.userprofile up ON ua.username = up.username
GROUP BY ua.username, first_name, last_name limit 100;
```

Now, by creating a view that combines the Redshift and external data, you can create a single entity that reflects both data sources. This can greatly simplify the data model for consumers of the data in Redshift.
```SQL
CREATE OR REPLACE VIEW local_weblogs.useractivity_byuser AS 
SELECT ua.username, first_name, last_name, COUNT(timestamp) 
FROM local_weblogs.useractivity ua
INNER JOIN weblogs.userprofile up ON ua.username = up.username
GROUP BY ua.username, first_name, last_name WITH NO SCHEMA BINDING;
```
*Note, the view requires `WITH NO SCHEMA BINDING` to link to the view to the external table.*

Now you can write a simple query to retrieve this expanded set of data.
```SQL
SELECT * FROM local_weblogs.useractivity_byuser LIMIT 100;
```

That concludes the Redshift component of the lab. Be sure to delete your Redshift cluster.

## Bonus Lab #3: AWS Database Migration Service (DMS) - Importing files from S3 to DynamoDB

AWS DMS is a cloud service that makes it easy to migrate relational databases, data warehouses, NoSQL databases, and other types of data stores. You can use AWS DMS to migrate your data into the AWS Cloud, between on-premises instances, or between combinations of cloud and on-premises setups. You can perform one-time migrations or can replicate ongoing changes to keep the source and targets in sync. 
AWS DMS supports a number of sources and targets for migration; for more details, refer to the <a href="https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Introduction.html" target="_blank">documentation</a>
As part of your data lake you might need to move data from on-premises or other locations into a centralized repository for analysis. As part of this workshop we will look at how you can leverage DMS to move a user profile dataset which is uploaded to S3 to DynamoDB

#### Prerequisites
You will need at least 2 IAM roles e.g. `dms-cloudwatch-logs-role` for pushing logs to Amazon CloudWatch and the `dms-vpc-role` for use by the DMS service. For more information on creating these roles, take a look at <a href="https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Security.APIRole.html" target="_blank">Creating the IAM Roles to Use with the AWS CLI and AWS DMS API</a> in the DMS documentation.
For DMS replication instance, you will need a VPC with subnets and security groups configured to allow access to AWS DMS services and othe AWS resources like S3 and DynamoDB. For more information, take a look at <a href="https://docs.aws.amazon.com/dms/latest/userguide/CHAP_ReplicationInstance.VPC.html" target="_blank">Setting Up a Network for a Replication Instance</a>

When you use Amazon S3 as a source for AWS DMS, the source Amazon S3 bucket that you use must be in the same AWS Region as the AWS DMS replication instance that you use to migrate your data. In addition, the AWS account you use for the migration must have read access to the source bucket. The role assigned to the user account creating the migration task must have S3 permissions for `GetObject` and `ListBucket`. For this workshop you can add these permissions to `dms-vpc-role`.
When working with a DynamoDB database as a target for AWS DMS, make sure that your IAM role allows AWS DMS to assume and grant access to the DynamoDB tables that are being migrated into. If you are using a separate role, make sure that you allow the DMS service to perform `AssumeRole`. The user account creating the migration task must be able to perform the DynamoDB actions `PutItem`, `CreateTable`, `DescribeTable`, `DeleteTable`, `DeleteItem`, and `ListTables`. For this workshop you can add these permissions to `dms-vpc-role`.

> **Note:** To keep it simple, for S3 and DynamoDB access you can leverage the AWS managed policies **AmazonS3FullAccess** and **AmazonDynamoDBFullAccess** and attach them to `dms-vpc-role` 

### Create DMS replication server, source and target endpoints and migration tasks
To perform a database migration, DMS needs a replication instance (which is a managed Amazon Elastic Compute Cloud (Amazon EC2) instance that hosts one or more replication tasks), source endpoint (an endpoint to access your source data store), target endpoint (an endpoint to access your target data store) and replication task(s) (task(s) to move a set of data from the source endpoint to the target endpoint)
You can create the above components either via AWS Management Console or via scripting e.g. Amazon CloudFormation. For this lab we will use an Amazon CloudFormation template to create the required components.

Here is the Amazon CloudFormation template that you can use to spin up the required components for DMS, <a href="https://us-east-1.console.aws.amazon.com/CloudFormation/home?region=us-east-1#/stacks/new?stackName=reinvent-2018-serverless-datalake-dms&templateURL=https://s3.amazonaws.com/arc326-instructions/script/serverlessdatalake2018-dms.yml" target="_blank">Create DMS stack</a>

Enter the stack name, choose the replication instance type, enter security group name, S3 bucket name (s3://^ingestionbucket^/raw/userprofile) and role arn to create the stack.

Once the stack creation is complete, open the [AWS DMS console](https://console.aws.amazon.com/dms/home) and explore the components that the Amazon CloudFormation template created. The CloudFormation will 

- Create a replication instance
- Create a source endpoint
- Create a target endpoint
- Create a target endpoint

> **Note:** For details on S3 source endpoint configuration, refer to <a href="https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Source.S3.html" target="_blank">AWS Documentation</a>. For details on DynamoDB endpoint configuration, refer to <a href="https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Target.DynamoDB.html" target="_blank">AWS Documentation</a>

#### Execute the DMS Task to load userprofile from S3 to DynamoDB

From the DMS console select the **Tasks** menu and select the task created via CloudFormation and click on **Start/Resume** to execute the task. The task status will change from *Ready* to *Starting* to *Running* to *Load complete*.
After the task is in *Load complete* status, open the DynamoDB console and verify that a new table `userprofile` was created with ~50000 user profile records.

#### Conclusion
As part of the above exercise we saw how to create a data load pipeline using DMS. You can extend the CloudFormation template to load multiple tables or change the target and source endpoints by simply swapping out the resources in the template.



# Clean Up

First, remove the Sagemaker Notebook. Once that completes you can go to the next step.

Open the Cloudformation Console and delete the workshop stack. If you leave the workshop running it will continue to generate data and incur charges.

**If you created a Redshift cluster or executed DMS lab, make sure to delete the cluster and dynamodb table!** Leaving these running can cost hundreds of dollars per month.

