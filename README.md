[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=20614650&assignment_repo_type=AssignmentRepo)
# <Your project name>

<Note - Replace all instructions within "<>" with your content>

## Project Overview 

### Business goal
<This section is the first thing that someone coming to the repo will read, so make a compelling reason why they should be interested in this project. This will likley align with why you are interested in the project.  Somes questions to think about and answer include:  What is the overall goal of the analysis?  Why are you undertaking it?  What specific questions do you plan to answer with the analysis?>

### Analysis approach
<What analysis approach will be used to meet your goal / answer your quetions?  At a base level, it will fall into the lifecycle categories of Analytics, ML, and Reverse ETL.  This section should identify the category and provide more details.  For example, for an analytics project you could describe an example plot(s) that you think will be useful. For an ML project, you could identify the target variable and features.>

### Data sources
<You need at least two data sources.  Ideally, all data sources can be accessed via an API or other automated means so that the ingestion can be fully automated.  At least one data source should be ‘dynamic’ where it is regularly refreshed with new data that needs to be ingested periodically.> 

#### <Your data source 1>
<Document your first data source.  Include an overview of the data source, the specific location (URL), expected access to the data, how it will be used for your analysis, etc.  Some technical content like number of columns and rows, data types, overall size of the data, refresh frequency, etc is appropriate also.>

#### <Your data source 2>
<Document your second data source.  Follow the guidance for data source 1.>

#### <Your additonal data source(s)>
<Document your additional data source(s) as needed.  Follow the guidance for data source 1.>

## Design - Data engineering lifecycle details
This project aligns with the data engineering lifecycle.  The lifecycle is the foundation of the book, <u>Fundamentals of Data Engineering</u>, by Joe Ries and Matt Hously.  A screenshot of the lifecycle from the book is shown below.

![Data Engineering Lifecycle](SupplementaryInfo/DataEngineeringLifecycle.png)

This design section describes how this project implements the data engineering lifecycle.

### Architecture and technology choices
<The default expectation is that you will use a lakehouse architectural approach for this project.  In most cases, the medallion architecture pattern will further clarify the data states and how the data is processed.  If your approach aligns with these expectations, simply stating that here will provide enough context for most readers (along with the details below).  If you are considering a different approach, then more elaboration is required (along with discussion with your instructor) >

### Data storage
<What is your data storage organization?  What file format(s) are you using?  What are the important considerations for storage in your solution?>

### Ingestion
<Design documentation for ingestion goes here.  Where does the data come from?  How is it ingested?  Where is it stored (be specific)?>

### Transformation
<Design documentation for transformation goes here.  What steps are required to transform the data from its original form? Where is it stored (be specific)?  Note - a transformation to an efficient data storage format such as delta lake is expected.>

### Serving
<Design documentation for serving goes here.  What steps are required to transform the initial transformation into a format optimal for your analysis approach? Where is it stored (be specific)?  >

## Undercurrents
<The data engineering lifecylce identifies several undercurrents.  Identify and document the undercurrents (at least two) that are most relevant to your project.  Explain why these are the most relevant.  Keep in mind that the people accessing the repo may not know about undercurrents, so provide some context.>

## Implementation

### Navigating the repo

### Reproduction steps
<The spirit of this effort is that someone else could start with this repo and reproduce your analysis.  Outline the steps required to do so in this section.  This should include a description of the repo layout to ease navigation.>