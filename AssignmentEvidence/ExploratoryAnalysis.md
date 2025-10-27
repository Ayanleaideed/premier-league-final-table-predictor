# Exploratory Data Analysis Report

## Dataset 1: Premier League Standings (API Data)

### Overview

- **Source:** Football-Data.org API
- **Seasons:** 2023-24, 2024-25
- **Total Records:** 40 (20 teams × 2 seasons)

### Data Structure

**Rows:**

- 2023-24: 20 teams
- 2024-25: 20 teams

**Columns:** 14

- position (integer)
- team_id (integer)
- team_name (string)
- team_short_name (string)
- team_tla (string)
- played_games (integer)
- won (integer)
- draw (integer)
- lost (integer)
- points (integer)
- goals_for (integer)
- goals_against (integer)
- goal_difference (integer)
- season (string)
- ingestion_date (string)

### Data Quality

**Missing Values:** None

**Duplicates:** 0

**Numeric Distributions (2024-25 season):**

- Played Games: 9 (all teams)
- Points: Range 2-22, Mean ~13.5
- Goals For: Range 5-17, Mean ~12
- Goals Against: Range 3-20, Mean ~11.5

**Sanity Checks:**

- Won + Draw + Lost = Played Games: ✓ Verified
- Points = (Won × 3) + Draw: ✓ Verified
- Goal Difference = Goals For - Goals Against: ✓ Verified

### Key Observations

- Data is clean and well-structured
- All mathematical relationships are correct
- No data quality issues identified
- Ready for analysis without transformation

---

## Dataset 2: Historical Match Data (CSV)

### Overview

- **Source:** Football-Data.co.uk
- **Seasons:** 2020-21 through 2024-25 (5 seasons)
- **Total Records:** 1,900 matches

### Data Structure

**Rows by Season:**

- 2020-21: 380 matches
- 2021-22: 380 matches
- 2022-23: 380 matches
- 2023-24: 380 matches
- 2024-25: 380 matches

**Columns:** 135 total (varies by season)

- Core columns present in all seasons: 95
- Additional columns in 2024-25: 27 (betting odds from new bookmakers)
- Columns only in older seasons: 13 (discontinued betting providers)

**Key Columns:**

- Date (string)
- HomeTeam (string)
- AwayTeam (string)
- FTHG - Full Time Home Goals (integer)
- FTAG - Full Time Away Goals (integer)
- FTR - Full Time Result (string: H/D/A)
- HS - Home Shots (integer)
- AS - Away Shots (integer)
- Plus 127 additional columns (mostly betting odds and statistics)

### Data Quality

**Missing Values:**

- Core match data (Date, Teams, Goals, Result): 0 missing
- Match statistics (Shots, Corners): Some missing in early seasons
- Betting odds columns: Significant missing values (expected)

**Duplicates:** 0

**Numeric Distributions:**

- Home Goals (FTHG): Min 0, Max 9, Mean ~1.5
- Away Goals (FTAG): Min 0, Max 6, Mean ~1.2
- Home Shots (HS): Min 0, Max 39, Mean ~13
- Away Shots (AS): Min 0, Max 32, Mean ~11

**Categorical Distributions:**

- Match Results (FTR):
  - Home Win (H): 46.2%
  - Draw (D): 25.1%
  - Away Win (A): 28.7%

**Unique Values:**

- Home Teams: 20 (correct for Premier League)
- Away Teams: 20 (correct for Premier League)

### Sanity Checks

**Result Verification:**

- Matches where FTR doesn't match score: 0 ✓
- Matches with negative goals: 0 ✓
- Matches with unrealistic scores (>10 goals): 0 ✓

**Data Consistency:**

- All 5 seasons have exactly 380 matches ✓
- Home advantage is visible in results (46% home wins) ✓
- Score distributions are realistic ✓

### Key Observations

- Core match data is complete and accurate
- Some auxiliary columns have missing values (not critical)
- Different seasons have different column sets due to changing data providers
- Result distribution shows expected home field advantage
- Data quality is good for analysis purposes

---

## Transformation Requirements

### For Next Phase (Silver Layer)

**Dataset 1 (Standings):**

1. No major transformations needed
2. Data is already clean and structured
3. May need to join with Dataset 2 on team names

**Dataset 2 (Historical Matches):**

1. **Date Formatting:** Convert Date column from string to date type
2. **Team Name Standardization:** Ensure team names match between datasets
   - Example: "Man United" vs "Manchester United"
3. **Column Selection:** Create filtered view with only core columns for analysis
   - Keep: Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR, HS, AS, key stats
   - Optional: Betting odds columns
4. **Handle Missing Values:**
   - Keep matches with complete core data
   - Fill or drop missing statistics based on analysis needs
5. **Feature Engineering:**
   - Calculate team form (last 5 matches)
   - Compute home/away performance metrics
   - Create rolling averages for goals scored/conceded

### Data Integration Strategy

1. Map team names between API standings and historical matches
2. Use team_id from API where possible
3. Create lookup table for team name variations
4. Filter historical data to only include current Premier League teams

---

## Conclusion

Both datasets are suitable for the planned analysis:

**Dataset 1 Strengths:**

- Clean, accurate, no missing data
- Current season data
- Includes team IDs for reliable joining

**Dataset 2 Strengths:**

- Large historical dataset (1,900 matches)
- Rich feature set for machine learning
- Consistent core data across all seasons

**Overall Assessment:**

- Data quality is good
- Minor transformations needed
- Ready to proceed to transformation phase
- Sufficient data for match outcome prediction modeling
