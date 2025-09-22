## Project Overview 

### Business goal
Soccer (football) is one of the most popular sports in the world, and the English Premier League (EPL) is especially interesting because it produces new data every week. I chose this topic because I enjoy following soccer and I think it would be fun to see how data can help explain team and player performance.  

The goal of my project is to look at Premier League match data together with a larger historical dataset from Kaggle. By combining these two sources, I want to understand what factors are most important in winning matches and also see how current teams compare with teams in the past.  

**Some questions I want to answer are:**
- What stats (like shots, possession, goals conceded) are most strongly related to winning?  
- Can simple models predict whether a team will win, lose, or draw a match?  
- Are there any players this season who are performing better or worse than expected compared to averages?  
- How do modern EPL teams compare to historical teams in European soccer?  

### Analysis approach
My project will use both **analytics** and **machine learning**.  

- First, I will do exploratory data analysis (EDA) with charts and summary statistics to see patterns in goals, shots, and other match stats.  
- Next, I will create features that combine recent match data with historical averages, like team form over the last 5 matches or home vs away performance.  
- Then I will train some simple classification models (for example logistic regression and random forest) to predict outcomes such as win/draw/loss.  
- Finally, I will evaluate the models using metrics like accuracy and ROC-AUC to see how well they work.  

This approach will let me tell a story about what matters most in soccer performance while also trying out some predictive modeling.

### Data sources

#### 1) Premier League Match Data API (Dynamic)
- **Overview:** This API provides up-to-date EPL match information, including fixtures, scores, standings, and sometimes player stats.  
- **Format/refresh:** JSON or CSV depending on how it’s pulled. It updates weekly as matches are played.  
- **How I will use it:** This is my dynamic dataset. I will use it to track the current EPL season and generate features like team form and recent performance.  
- **URL:** [Football-Data.org](https://www.football-data.org/)  

#### 2) European Soccer Database (Kaggle) — Static
- **Overview:** This Kaggle dataset includes 25,000+ matches and 10,000+ players from 2007–2016 across European leagues. It has results, team stats, and player attributes.  
- **Format/size:** SQLite/CSV (~300 MB).  
- **How I will use it:** This is my static dataset. It gives me historical data that I can compare to the current EPL season to find longer-term trends.  
- **URL:** [Kaggle Soccer Dataset](https://www.kaggle.com/datasets/hugomathien/soccer)  
