# Virus-Scripts
Code to create comparable trends in virus across states

The virus being an occasion for everyone to make charts and learn to code, I made this file to compare key virus metrics (cases, deaths, hospitalizations and test positivity) 
across groups of states. Cases and deaths data come from the Johns Hopkins Center for Systems Science and Engineering github, and hospitalizations and test positivity came from
the Covid Tracking Project (which ceased data collection on March 7, 2021, and I haven't yet incorporated a new data source cleanly enough to post, so those trends stop then). 

As currently configured, the program sums each of those virus metrics and total population by group of states, and then shows 7-day moving average percent of population trends.
I could go with the per 100,000 easily enough, but percent of population is easier for me to think about in certain ways.
