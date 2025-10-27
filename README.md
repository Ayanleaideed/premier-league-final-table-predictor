# Premier League Match Prediction Project

## Project Overview

### Business goal

Soccer is one of the most popular sports in the world, and the English Premier League produces new data every week. I chose this topic because I follow soccer and wanted to see how data analysis could help understand team performance and potentially predict match outcomes.

The goal is to analyze Premier League match data from multiple sources to identify what factors are most important in winning matches and build a model to predict match outcomes.

**Note:** This project focuses on team-level analysis rather than individual players to keep the scope manageable.

**Key questions:**

- What team statistics are most strongly related to winning?
- Can I build a model to predict match outcomes (win/draw/loss)?
- How do teams perform over multiple seasons?

### Analysis approach

This project uses both analytics and machine learning on team-level data.

- Exploratory data analysis to identify patterns in team performance
- Feature engineering based on team form, home/away performance
- Classification models (logistic regression, random forest) to predict outcomes
- Model evaluation using accuracy and confusion matrices

### Data sources

#### Data Source 1: Football-Data.org API (Dynamic)

- **Overview:** REST API providing current Premier League standings and match data
- **Format:** JSON, updates weekly as matches are played
- **Usage:** Current season data (2023-24, 2024-25 seasons)
- **URL:** <https://www.football-data.org/>
- **Access:** Free API key with rate limiting (10 requests/minute)
- **Data includes:** Team standings, wins, losses, draws, goals for/against, points

#### Data Source 2: Football-Data.co.uk Historical Data (Static)

- **Overview:** Historical match results and statistics for Premier League
- **Format:** CSV files, one per season
- **Usage:** Historical match data for 5 seasons (2020-21 through 2024-25)
- **URL:** <http://www.football-data.co.uk/englandm.php>
- **Data includes:** Match results, scores, shots, corners, fouls, betting odds
- **Note:** Originally planned to use Kaggle dataset, but it was outdated (only through 2016) and had missing data, so switched to this more current and complete source

## Design - Data engineering lifecycle details

![Data Engineering Lifecycle](SupplementaryInfo/DataEngineeringLifecycle.png)

Figure: Data engineering lifecycle for this project — shows ingestion (Bronze), transformation/cleaning (Silver), feature/aggregation and serving (Gold), plus orchestration and monitoring.
This project follows the data engineering lifecycle from *Fundamentals of Data Engineering*

### Architecture and technology choices

Using a lakehouse architecture with the medallion pattern (Bronze, Silver, Gold layers).

**Platform:** Azure Databricks Community Edition (free version)

**Key technologies:**

- Azure Cloud (Azure Databricks for compute and orchestration)
- Azure Storage — Blob Storage / Data Lake Storage Gen2 for raw and curated data
- Azure Databricks (notebooks, clusters, workspace catalog)
- Delta Lake (transactional storage format, medallion pattern)
- PySpark (ingestion and transformations)
- Python (data manipulation, analysis, and machine learning)
- Databricks workspace catalog (table and schema management)
- Azure Key Vault (secure storage for API keys and secrets)
- Git (version control; integrate with Databricks Repos for CI/CD)

### Data storage

Using Delta Lake tables in Databricks workspace catalog with the following schema structure:

**Bronze Layer (Raw Data):**

```
workspace
  └── premier_league_bronze
      ├── pl_standings_2023 (Delta table)
      ├── pl_standings_2024 (Delta table)
      └── pl_matches_historical (Delta table)
```

**Silver Layer (Cleaned Data):**

```
workspace
  └── premier_league_silver
      └── <Will be defined in transformation phase>
```

**Gold Layer (Aggregated/Feature Data):**

```
workspace
  └── premier_league_gold
      └── <Will be defined in serving phase>
```

**Storage approach:**

- Bronze layer: Raw data stored as Delta tables
- API data: Separate tables per season
- Historical data: Combined table with all seasons
- Metadata added: season name, ingestion timestamp

### Ingestion

#### Data Source 1: Football-Data.org API

**Implementation:** PySpark notebook in Databricks (`src/ingestion/DataSet1.ipynb`)

**Process:**

1. Retrieve API key from Databricks secret scope (secure storage)
2. Make REST API calls to get standings data
3. Transform nested JSON to flat structure
4. Add metadata (season, ingestion date)
5. Save to Delta tables in Bronze schema

**API endpoints used:**

- `/v4/competitions/PL/standings?season=2023` (2023-24 season)
- `/v4/competitions/PL/standings?season=2024` (2024-25 season)

**Output tables:**

- `workspace.premier_league_bronze.pl_standings_2023`
- `workspace.premier_league_bronze.pl_standings_2024`

**Key features:**

- Programmatic access via requests library
- API key stored securely in Databricks secrets
- Flattens nested JSON structure into tabular format
- Delta format for reliability

#### Data Source 2: Football-Data.co.uk CSV Files

**Implementation:** PySpark notebook in Databricks (`src/ingestion/DataSet2.ipynb`)

**Process:**

1. Download CSV files for 5 seasons programmatically
2. Convert to Spark DataFrames
3. Add metadata (season name, ingestion date)
4. Combine all seasons using unionByName with allowMissingColumns
5. Save to single Delta table

**Seasons ingested:**

- 2020-21 (season code: 2021)
- 2021-22 (season code: 2122)
- 2022-23 (season code: 2223)
- 2023-24 (season code: 2324)
- 2024-25 (season code: 2425)

**Output table:**

- `workspace.premier_league_bronze.pl_matches_historical`
- Total records: 1,900 matches (380 per season)

**Data handling notes:**

- Different seasons have different numbers of columns (108-122 columns)
- Used unionByName with allowMissingColumns to preserve all columns
- Missing columns filled with NULL values automatically
- Total column count in combined table: 135 columns

### Transformation

<Placeholder - Will be completed in next assignment>

### Serving

<Placeholder - Will be completed in next assignment>

## Undercurrents

### Data Management

Important because I'm combining two different data sources:

- Need to standardize team names between datasets
- Track data quality and identify missing values
- Maintain data lineage for debugging
- Version control for code

### Orchestration  

Relevant because API updates weekly:

- Can schedule automated ingestion (if needed in future)
- Ensure data pipelines run in correct order
- Handle API errors or downtime
- Currently running manually but designed for automation

## Implementation

### Navigating the repo

```
/src
  /ingestion
    - DataSet1.ipynb (API ingestion)
    - DataSet2.ipynb (CSV ingestion)
    - ExploratoryAnalysis.ipynb (EDA)
/SupplementaryInfo
  - ExploratoryAnalysis.md (EDA report)
  - Screenshots (evidence of successful ingestion)
README.md
```

### Reproduction steps

**Prerequisites:**

- Azure Databricks Community Edition account
- Football-Data.org API key

**Steps:**

1. Clone this repository
2. Set up Databricks workspace
3. Create secret scope and store API key:

```
   databricks secrets create-scope api-keys
   databricks secrets put-secret api-keys football-api-key --string-value "YOUR_KEY"
```

4. Run `src/ingestion/DataSet1.ipynb` to ingest API standings data
5. Run `src/ingestion/DataSet2.ipynb` to ingest historical match data
6. Run `src/ingestion/ExploratoryAnalysis.ipynb` to analyze datasets
7. Review tables in `workspace.premier_league_bronze` schema

**Output:**

- Three Delta tables in Bronze layer
- Exploratory analysis report in SupplementaryInfo folder
