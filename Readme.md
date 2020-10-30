# AWS Timetracking Automation from csv

## Setup

Change this line. `csv_file` should be the path to your local file.
```python
csv_file = 'CHANGE IT'
```

Change also this line. `ap_` should be the AP with your most hours. (like `AP 3`)
```python
ap_ = 'CHANGE IT'
``` 

## How to run it

Open the excel sheet where you want to insert the time tracking. 
Open also the correct spreadsheet. Click in a writable cell!
Important...Dont close excel. it needs to be open...
Then just start the application! 

## Adding Git logs

just run this in all your repositories. Save all the logs in one folder  
`git log --all --pretty=format:'%ai,%s' > log.csv`