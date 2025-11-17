# Premier League Table Prediction

## Project Overview

### Business Goal

Football fans and analysts spend a lot of time debating where teams will finish in the Premier League table. Most predictions are just gut feelings or basic assumptions like "the big teams always win." I want to build something better - a data-driven model that can actually predict final standings based on real performance metrics.

The main goal is to answer: can we predict Premier League final table positions more accurately than simple methods by using historical data and machine learning? Specifically, I'm trying to figure out what actually matters for team success. Is it recent form? Goal difference? Home advantage? Previous season performance?

This matters because accurate predictions could help fans make better fantasy football decisions, give analysts a baseline to compare against, and just generally make watching the season more interesting when you can track how teams are doing versus expectations.

The questions I want to answer:

- Can a model beat the "teams finish where they did last year" baseline?
- What features actually predict success (goals scored, recent form, etc.)?
- How early in the season can we make accurate predictions?
- Do promoted teams follow predictable patterns?

### Analysis Approach

This is a machine learning project, specifically supervised learning regression. I'm predicting a continuous target variable (total points at season end) and then converting that to table positions.

**Target Variable:** Final season points total for each team

**Key Features:**

- Rolling averages for recent form (last 5 and 10 games)
- Goal statistics (scored, conceded, difference)
- Home vs away performance splits
- Previous season final position
- Current position and trends
- Schedule difficulty metrics

**Model Choice:** Random Forest Regressor - it handles the mix of features well, doesn't need much preprocessing, and gives feature importance so I can see what actually matters. If that doesn't work well, I'll try XGBoost.

**Validation:** I'll train on seasons 2021-2024 and test on 2024-2025. Success means beating simple baselines and getting predictions within 5 points per team on average.

### Data Sources

#### Data Source 1: Premier League Historical Standings

**Overview:** Complete season-by-season standings data for all 20 Premier League teams from 2021-2022 through 2025-2026 seasons.

**Location:** <https://www.football-data.co.uk/mmz4281> (programmatically downloaded)

**Access:** Automated download via Python script in Databricks, stored in Azure Data Lake Storage under `workspace.premier_league_bronze`

**Contents:**

- Team names, season identifiers
- Match results (wins, draws, losses for each team)
- Goals scored and conceded (total and by match)
- Home and away splits for all statistics
- Final points and table positions
- Approximately 100 teams across 5 seasons (20 teams per season)

**How It's Used:** This is the core dataset. I'll use it to create all the features (rolling averages, form metrics, etc.) and train the model. Each row represents a team's full season performance.

**Refresh Frequency:** Downloaded programmatically, can be updated weekly during an active season

**Size:** Around 500KB total across all CSV files, easily handled by Databricks

#### Data Source 2: Match-by-Match Results

**Overview:** Individual match results with dates, teams, scores, and outcomes for the same time period.

**Location:** <https://www.football-data.co.uk/mmz4281> (programmatically downloaded)

**Access:** Automated download via Python script in Databricks, stored in Azure Data Lake Storage

**Contents:**

- Match dates and gameweek numbers
- Home team, away team, final score
- Half-time scores
- Around 380 matches per season (2000+ total matches)

**How It's Used:** This lets me calculate time-based features like "form in last 5 games" or "goals scored in last 10 games." I'll aggregate this up to team-season level after creating rolling statistics.

**Refresh Frequency:** Static historical data, updated at season end

**Size:** About 1-2MB total

## Design - Data Engineering Lifecycle Details

This project follows the data engineering lifecycle as outlined in *Fundamentals of Data Engineering* by Joe Reis and Matt Housley. The lifecycle provides a framework for moving data from source to analysis.

![Data Engineering Lifecycle](SupplementaryInfo/DataEngineeringLifecycle.png)

### Architecture and Technology Choices

I'm using a lakehouse architecture with the medallion pattern (bronze, silver, gold layers). This makes sense for this project because I need to preserve raw data, clean and transform it, then create analysis-ready datasets.

**Tech Stack:**

- Azure Databricks for scalable data processing and machine learning workflows
- Azure Data Lake Storage for organizing data in bronze/silver/gold layers
- Parquet format for processed data (efficient storage and fast reads)
- MLflow for model tracking and serialization within Databricks
- Flask for the serving layer (can be deployed on Azure App Service)
- Python (pandas, scikit-learn) for data manipulation and modeling within Databricks notebooks

The lakehouse approach works here because I have structured data that needs multiple transformation stages, and I want to keep each stage separate so I can rerun parts without starting from scratch.

### Data Storage

**Organization:**

```
workspace.premier_league_bronze/     # Raw CSV files in Azure Data Lake
├── season_2021_2022.csv
├── season_2022_2023.csv
├── season_2023_2024.csv
├── season_2024_2025.csv
├── season_2025_2026.csv
└── matches_2021_2026.csv

workspace.premier_league_silver/     # Cleaned and standardized data
├── standings_cleaned.parquet
└── matches_cleaned.parquet

workspace.premier_league_gold/       # Feature-engineered, analysis-ready data
└── training_features.parquet
```

**File Formats:**

- Bronze: CSV (original format from football-data.co.uk, stored in Azure Data Lake)
- Silver: Parquet (compressed, typed, faster to read)
- Gold: Parquet (optimized for model training)

**Storage Considerations:**

- All data stored in Azure Data Lake Storage organized by schema (bronze/silver/gold)
- Keep all three layers so I can rebuild if feature engineering changes
- Parquet gives 10x compression vs CSV and loads way faster in Databricks
- Version control through Databricks workspace and schema naming
- Gold layer gets regenerated if features change

### Ingestion

**Source to Bronze:**

Data is ingested programmatically from football-data.co.uk using Python within a Databricks notebook. The source URL is `https://www.football-data.co.uk/mmz4281`.

**Process:**

1. Databricks notebook runs a Python script to download CSV files from football-data.co.uk
2. Downloads season standings CSVs (one file per season: 2021-2026)
3. Downloads combined match results CSV covering all seasons
4. Saves directly to Azure Data Lake Storage under `workspace.premier_league_bronze` schema
5. Logs ingestion date, source URL, and file metadata in a separate tracking table

**Configuration:**

```python
BASE_URL = "https://www.football-data.co.uk/mmz4281"
PROJECT = "premier_league"
SCHEMA_BRONZE = f"workspace.{PROJECT}_bronze"
```

**Data Validation at Ingestion:**

- Check that CSV has expected columns
- Verify row counts match expected (20 teams per season, 380 matches per season)
- Flag any obvious issues before moving to silver layer
- Log any download failures or incomplete files

### Transformation

**Bronze to Silver (Cleaning):**

This is where I standardize team names, fix data types, handle missing values, and validate the data makes sense.

**Steps:**

1. Load all bronze CSV files
2. Standardize team names (fix spelling inconsistencies, handle team name changes)
3. Convert columns to correct types (dates to datetime, goals to int, etc.)
4. Remove duplicate records
5. Handle missing values:
   - Drop rows missing critical data (match results, goals)
   - Fill missing non-critical fields with defaults
6. Add validation checks:
   - Total wins + draws + losses = games played
   - Goals for across all teams = goals against across all teams
   - Points calculation is correct (3 * wins + draws)
7. Save to silver layer as parquet files

**Silver to Gold (Feature Engineering):**

This is where I create the actual features the model will use.

**Features Created:**

1. **Form Metrics**
   - Sort matches by date for each team
   - Calculate rolling 5-game and 10-game points averages
   - Calculate rolling goal difference
   - Win percentage over rolling windows

2. **Aggregate Statistics**
   - Goals per game (total, home, away)
   - Clean sheets percentage
   - Average goal difference per game

3. **Position Features**
   - Current table position
   - Position change from 5 games ago
   - Points gap to 4th place (Champions League)
   - Points gap to 18th place (relegation)

4. **Historical Features**
   - Previous season final position
   - Previous season points total
   - Indicator for promoted teams

5. **Schedule Features**
   - Strength of remaining opponents
   - Home games remaining vs away games

**Storage:** Save as `training_features.parquet` in gold layer. Each row is a team-season with all features and the target variable (final points).

**Handling Edge Cases:**

- Promoted teams: Create features based on Championship average or previous promoted teams
- First few games of season: Rolling averages start at 0 or use previous season baseline
- Missing historical data: Use league average for that season

### Serving

**Gold to Model Training:**

The gold layer data is already in the right format for scikit-learn. Load the parquet, split into features (X) and target (y), and train.

**Training Process:**

1. Load `training_features.parquet` from gold layer in Azure Data Lake
2. Split by season (not random) - use 2021-2024 for training, 2024-2025 for testing
3. Separate features (X) from target variable (y = final points)
4. Train Random Forest model with cross-validation in Databricks
5. Evaluate on test set
6. Track model with MLflow (saves model, metrics, parameters automatically)
7. Register best model in MLflow Model Registry

**Model to Application:**

The Flask app (deployed on Azure App Service) loads the trained model from MLflow Model Registry and uses it to make predictions on new data.

**Endpoints:**

- `POST /predict` - Takes current season data, calculates features, returns predicted table
- `GET /model-info` - Returns model accuracy metrics and feature importance from MLflow
- `GET /` - Homepage with input form

**Prediction Pipeline:**

1. User inputs current gameweek and standings data (or app pulls from API in future)
2. Backend calculates all required features using same process as training
3. Load registered model from MLflow Model Registry (cached in memory for speed)
4. Model predicts final points for each team
5. Convert points to positions (sort, handle tiebreakers)
6. Return JSON with predicted table and confidence intervals
7. Frontend displays results in a nice table format

**Deployment:**

- Flask app can be deployed to Azure App Service or run locally for testing
- Model loaded from MLflow Model Registry
- Connected to Azure Data Lake for any additional data needs

**Performance:**

- Model cached in memory after first load from MLflow
- Predictions should take less than 1 second
- Log all predictions for later analysis
- MLflow tracking provides automatic performance monitoring

**Prediction Logging and Model Evaluation:**

To track model performance in production and enable future improvements, all predictions are logged and stored for evaluation:

1. **Prediction Storage:**
   - Each prediction request is logged with timestamp, input features, and predicted outcomes
   - Stored in a separate Delta table: `workspace.premier_league_predictions`
   - Includes metadata like model version used (from MLflow), confidence scores, and request details

2. **Evaluation Pipeline:**
   - Once actual season results are available, compare logged predictions against real outcomes
   - Calculate metrics like mean absolute error, top 4 accuracy, relegation zone accuracy
   - Track model drift over time (is the model getting worse as seasons progress?)
   - Store evaluation results in `workspace.premier_league_metrics` table

3. **Feedback Loop:**
   - Use logged predictions and actual results to retrain model with new data
   - Identify which features are becoming more/less important over time
   - Detect systematic biases (consistently over/underpredicting certain teams)

**Schema for Prediction Logging:**

```python
prediction_log = {
    'prediction_id': 'unique_id',
    'timestamp': 'datetime',
    'model_version': 'mlflow_model_version',
    'gameweek': 'current_gameweek',
    'team_predictions': [{
        'team_name': 'team',
        'predicted_points': 'points',
        'predicted_position': 'position',
        'confidence_interval': 'range'
    }],
    'actual_results': 'filled_in_later'
}
```

This logging system lets me evaluate how well the model performs in real scenarios and continuously improve it based on actual results.

## Undercurrents

The data engineering lifecycle identifies several undercurrents that cut across all stages. Here are the three most relevant to this project:

### 1. Data Quality

**What It Is:**
Data quality means the data is accurate, complete, consistent, and reliable. For this project, it covers whether the match results are recorded correctly, team names are consistent, and there are no weird errors in the stats.

**Why It Matters Here:**
Football data comes from different sources and sometimes has errors - misspelled team names, missing matches, incorrect scores, or teams recorded under old names. If I train on bad data, the model learns wrong patterns. Even small issues like one team having the wrong number of wins will throw off predictions.

**What I'm Doing:**

- Cross-checking data against official Premier League records for a sample of matches
- Building validation rules within Databricks notebooks (like making sure total games = wins + draws + losses)
- Manually fixing team name inconsistencies before processing
- Logging any data issues I find and documenting how I fixed them in Azure Data Lake
- Keeping the bronze layer unchanged so I can always go back to raw data
- Running automated checks after each transformation stage
- Leveraging Databricks' built-in data quality checks

**Specific Validation Checks:**

- Validate that sum of all team points equals expected total for the season
- Check that goals for across all teams equals goals against across all teams
- Make sure no team has impossible stats (like negative goals or more than 38 games played)
- Verify promoted teams are marked correctly each season
- Flag any teams with suspicious win/loss patterns that might indicate data errors

### 2. Data Management

**What It Is:**
Data management is about organizing, storing, and versioning data properly. It includes decisions about file formats, folder structure, and keeping track of what data you have and where it came from.

**Why It Matters Here:**
With five seasons of data, multiple transformation stages, and different feature sets, things can get messy fast. If I don't organize properly, I'll lose track of which version of the data I used to train which model. Also, if I want to add new features later, I need to be able to regenerate the gold layer without starting from scratch. Azure Data Lake and Databricks workspaces provide structure but still need proper organization.

**What I'm Doing:**

**Current Implementation:**

- Organizing code and notebooks in a clear structure
- Using descriptive naming for files and variables
- Documenting transformation steps in notebook markdown cells
- Keeping track of which data files are used where

**Future Enhancements (Planned):**

While the current implementation uses a simplified approach suitable for development and testing, these features are planned for future updates when scaling up:

- Full medallion architecture (bronze/silver/gold) organized as separate schemas in Azure Data Lake
- Each transformation stage saved in its own schema with clear naming conventions
- Parquet format for all processed data (smaller files, faster reads in Databricks)
- MLflow tracking for all model versions, parameters, and metrics
- Databricks notebooks version controlled through Git integration
- Metadata tables logging when data was ingested and from where
- Separate tracking for each training run in MLflow (no overwriting)
- Databricks job scheduling for automated pipeline runs

These enhancements will improve scalability, reproducibility, and maintainability as the project grows.

### 3. Security and Privacy

**What It Is:**
Security is about protecting data from unauthorized access. Privacy is about handling personal information responsibly. Even though this seems less relevant for public football statistics, there are still considerations.

**Why It Matters Here:**
The football stats themselves are public, but when I build the web app, user interactions could contain personal info (IP addresses, prediction requests, potentially user accounts in the future). Also, I need to respect the data sources' terms of service and not overload their servers or use the data in ways they don't allow. Azure provides security features but they need to be configured properly.

**What I'm Doing:**

- Checking terms of service for football-data.co.uk to make sure I can use the data this way
- Not storing any user personal information in the app (no accounts required)
- Using Azure's built-in security features (access controls, encryption at rest)
- Configuring proper authentication for Databricks workspace access
- Rate limiting the prediction endpoint so the app can't be abused
- Using HTTPS when deployed to Azure App Service
- Not scraping data too aggressively from sources (respecting robots.txt and rate limits)
- Documenting data sources clearly so users know where predictions come from
- Azure Data Lake access controlled through proper permissions and service principals

## Implementation

### Navigating the Repo

```
premier-league-prediction/
├── databricks_notebooks/
│   ├── 01_ingestion.py              # Download data to bronze layer
│   ├── 02_bronze_to_silver.py       # Cleaning and validation
│   ├── 03_silver_to_gold.py         # Feature engineering
│   └── 04_model_training.py         # Training and MLflow tracking
├── app/
│   ├── app.py                       # Flask application
│   ├── templates/
│   │   ├── index.html               # Homepage
│   │   └── results.html             # Predictions display
│   └── static/
│       └── style.css                # Basic styling
├── config/
│   └── config.py                    # Configuration variables
├── SupplementaryInfo/
│   └── DataEngineeringLifecycle.png
├── tests/
│   └── test_features.py             # Unit tests for feature engineering
├── requirements.txt                 # Python dependencies
└── README.md
```

**Note:** Data and models are stored in Azure (Data Lake Storage and MLflow), not in the repo.

### Reproduction Steps

If you want to reproduce this analysis from scratch:

**1. Set Up Development Environment**

**Option A: Using Free Databricks Community Edition (Recommended for Development)**

- Sign up for free Databricks Community Edition at community.cloud.databricks.com
- No Azure subscription needed for initial development
- Data stored locally in Databricks File System (DBFS)

**Option B: Using Azure (For Production/Scaling)**

- Create an Azure Databricks workspace
- Set up Azure Data Lake Storage Gen2 account
- Configure access permissions between Databricks and Data Lake

**Option C: Using Google Colab**

- Use Google Colab for model training if you need more compute power
- Store data in Google Drive or download directly in the notebook
- Export trained model to use in Flask app

**2. Clone the Repository**

```bash
git clone [TBD]
cd premier-league-prediction
```

**3. Set Up Notebooks**

**For Databricks:**

- Import notebooks from `databricks_notebooks/` folder into your workspace
- Update `config/config.py` with your storage details (or use local paths for Community Edition)
- Install required libraries in your cluster

**For Google Colab:**

- Upload notebooks to Google Drive
- Install required libraries in the notebook (`!pip install pandas scikit-learn mlflow`)
- Adjust file paths to work with Google Drive or direct downloads

**4. Run Ingestion**
Open and run `01_ingestion.py`:

- Downloads data from football-data.co.uk
- Saves to local storage or cloud storage depending on setup
- Validates file completeness

**5. Run Transformations**

Bronze to Silver (run `02_bronze_to_silver.py`):

- Reads from bronze layer
- Cleans and validates data
- Saves to silver layer

Silver to Gold (run `03_silver_to_gold.py`):

- Reads from silver layer
- Engineers all features
- Saves to gold layer

**6. Train the Model**
Run `04_model_training.py`:

- Loads gold layer data
- Trains Random Forest model
- Tracks everything in MLflow (if using Databricks/Colab with MLflow setup)
- Saves trained model locally or to model registry

**7. Run Web App Locally**

```bash
cd app
uv pip install -r requirements.txt
uv run uvicorn app:app --host 0.0.0.0 --port 5000
```

**Note:** This assumes you have `uv` installed. `uv` will handle the installation of dependencies from `requirements.txt` and run the `uvicorn` server within the correct environment.

The app will run on `http://localhost:5000`. Open this URL in your browser to test predictions.

**Requirements:**

- Azure subscription with Databricks and Data Lake Storage (or use free Databricks Community Edition for development)
- Alternatively, Google Colab can be used for model training if additional compute is needed
- Python 3.9 or higher
- Databricks Runtime 13.0+ recommended (if using Databricks)
- Libraries: pandas, numpy, scikit-learn, mlflow, flask

**Note on Infrastructure:**
This project is designed to work with the free Databricks Community Edition for development and testing. The Azure components (Data Lake Storage, App Service) can be added later if you want to scale up or deploy to production. For now, local storage and development servers work fine for getting the model trained and tested.

**Expected Runtime:**

- Ingestion: 2-3 minutes (downloads files)
- Bronze to Silver: 1-2 minutes
- Silver to Gold: 2-3 minutes  
- Model training: 5-10 minutes (includes cross-validation and MLflow logging)

**Troubleshooting:**

- If ingestion fails, check internet connection and football-data.co.uk availability
- For Community Edition users: if storage quota is exceeded, clean up old files or use local download
- If using Google Colab: make sure to mount Google Drive if storing data there
- If Azure access fails (when using paid tier): verify Databricks has permissions to Data Lake Storage
- Make sure cluster/notebook has required libraries installed
- If MLflow tracking fails: check that MLflow is properly configured (or skip MLflow and just save model locally for testing)
- For local Flask app: make sure port 5000 isn't already in use

**Development Notes:**

- Start with the free options (Databricks Community Edition or Google Colab) to get everything working
- Azure components can be added later when you're ready to scale or deploy
- The core ML pipeline works the same regardless of infrastructure choice
- Focus on getting the model training and predictions working first, optimize infrastructure later

That's it. Once you've run through these steps, you'll have a trained model and working web app for Premier League predictions. Let's go.......
