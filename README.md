# Serverless Data Lake Workshop
Welcome to the serverless data lake workshop. In this workshop, you will create a serverless data lake that combines the data from an e-commerce website, customer profile database, and demographic data.


## Backstory

You are playing the role of the data lake architect and your primary customers are the analytics and BI team for the e-commerce website. They want to learn about customer behaviors from a variety of data sources across the enterprise. The current data warehouse is too rigid and doesn't offer the flexibility to explore and visualize data across different silos within the enterprise. Your job is to work with the cloud engineering team, the teams that support the source systems, and the analytics team to give them the tools they need to help grow the business.

### Current Challenges

The current data warehouse is very rigid in its star schema architecture. It is very difficult to get new data into the warehouse and have it linked up to other data sources. The result is a set of data marts that are isolated from one another. Another challenge is that there are a lot of semi-structured data sources that the current data warehouse team cannot process. For example, data is pulled from the weblog JSON files into a relational database, but only a subset of the data fits into the existing schema and the rest is lost. If the requirements change, it is very difficult and time-consuming to change the schema, and the historical data is lost since the source files are not kept.

### The Cloud Engineering Team

The cloud engineering team has put together a set of resources that you can use to build out the data lake. They practice infrastructure as code, so all the components are created using a set of cloud formation scripts that are available in this git repository.

These resources include the basics of the data lake such as S3 buckets, as well as IAM roles that will be needed to access the services.

When a CloudFormation script completes execution, it returns a set of Outputs that provide details on the resources that were created. 

In order to complete the lab, you will need to be familiar with where to find these outputs and how to use them in the lab. Once you create the CloudFormation stack, spend a little time navigating the console to find these outputs.

### Why a Data Lake
A data lake is the central repository for all data in the enterprise. It ingests data from a variety of data sources and stores them in the lake in the format they arrive without losing data. ETL processes will transform the data into a prepared state, either as files optimized for query such as ORC or parquet, or into Redshift, an MPP Data warehouse with many nodes.

#### Separation of Data and Compute
Traditional data warehouses store data on database clusters that both store the data and perform the operations on the data. This leads to a challenge as the dataset grows: Do you optimize your resources for compute or storage? 

By storing the data on Amazon S3, you have a cost-effective service that can store virtually unlimited amounts of data. Around S3 is an ecosystem of tools that enable direct querying of the data, or high-performance loading into a database cluster. This also permits the creation of transient clusters that spin up to perform the computations and spin down when they are complete.

## Why Serverless
* Simple to manage
* No cost for idle
* Agile

# Setup

> ***For this lab, ensure the current AWS region is US East (N. Virginia).***

Here is the Amazon CloudFormation script that the cloud engineering team made available. <a href="https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=reinvent-2018-serverless-datalake&templateURL=https://s3.amazonaws.com/arc326-instructions/script/serverless-data-lake.yaml" target="_blank">Create a stack</a> This template will provide a head start in configuring the data lake.

[Annotated CloudFormation Template ](serverlessdatalake2018.html)

## High Level Serverless Data Lake Architecture

![data lake architecture](/images/datalakearc.png)

## Serverless Data Lake Components
* S3
* DynamoDb
* Athena
* Lambda
* Kinesis Firehose
* Quicksight
* Cloudwatch Logs


<details><summary>Component Details</summary>
<p>

# Storage
The separation of data and compute is a foundation architectural concept in modern data lakes. By using S3 as the storage tier, you can have transient data warehouse or Hadoop clusters that scale up to the compute capacity when you need them.

## Simple Storage Service (S3)
Amazon S3 is object storage built to store and retrieve any amount of data from anywhere – websites and mobile apps, corporate applications, and data from IoT sensors or devices. It is designed to deliver 99.999999999% durability and stores data for millions of applications used by market leaders in every industry.

S3 is the cornerstone of a data lake; it provides the storage tier for data at rest. Data in S3 can be queried in place using Athena or Redshift Spectrum, mounted to Hadoop with EMR, and loaded into Redshift.

## Amazon Redshift
Amazon Redshift is a fast, scalable data warehouse that makes it simple and cost-effective to analyze all your data across your data warehouse and data lake. Redshift delivers ten times faster performance than other data warehouses by using machine learning, massively parallel query execution, and columnar storage on high-performance disk.

Redshift is integrated with S3 to allow for high-performance parallel data loads from S3 into Redshift. 

# Ingestion  

## Kinesis Data Firehose
Amazon Kinesis Data Firehose is the easiest way to load streaming data into data stores and analytics tools. It can capture, transform, and load streaming data into Amazon S3, Amazon Redshift, Amazon Elasticsearch Service, and Splunk, enabling near real-time analytics with existing business intelligence tools and dashboards you’re already using today. It is a fully managed service that automatically scales to match the throughput of your data and requires no ongoing administration. It can also batch, compress, and encrypt the data before loading it, minimizing the amount of storage used at the destination and increasing security.

## Relational Databases
Relational database systems form the backbone of most enterprise data systems. The data lake will receive data from the relational databases on a periodic basis, either through a data stream such as Kinesis Firehouse, 3rd-party tools like Sqoop, or through change data capture (CDC) using Amazon Database Migration Service (DMS). These data changes will be pushed into the ingestion buckets in the data lake for later processing. In this lab, we will copy data into S3 to simulate the ingestion of data from a CDC service like DMS. 

## Third Party Data
Frequently, data that comes from outside the organization will be valuable to integrate into the data lake. In this example, demographic data from the US Census bureau curated by a third party will be included in the data for analysis. The data will be staged into S3 during startup by the CloudFormation script, but this data can be sourced through a variety of channels.

# Data Catalog
## Glue Data Catalog
The AWS Glue Data Catalog contains references to data that is used as sources and targets of your extract, transform, and load (ETL) jobs in AWS Glue. To create your data warehouse, you must catalog this data. The AWS Glue Data Catalog is an index to the location, schema, and runtime metrics of your data. The AWS Glue Data Catalog is Hive compatible so it can be used with Athena, EMR, and Redshift Spectrum in addition to Glue ETL.

You can add table definitions to the AWS Glue Data Catalog in the following ways:
* Run a crawler that connects to one or more data stores, determines the data structures, and writes tables into the Data Catalog. You can run your crawler on a schedule.
* Use the AWS Glue console to create a table in the AWS Glue Data Catalog. 

</p>
</details>

## Final Setup
Once the CloudFormation stack has completed loading, you will need to run a lambda function that loads the data into the ingestion bucket for the user profile.

1. Open the CloudFormation Console and load the *stackname* stack.
1. Expand the Outputs Section and look for ```WorkshopInstructionsUrl```
1. Click the link to open the lab instructions.



