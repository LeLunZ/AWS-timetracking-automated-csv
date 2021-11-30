# Timetracking Automation from csv

## Setup

```bash
pip3 install -r requirements.txt
```

## CSV Export

Open the commandline.
Run with python >= 3.9:
```bash
python3 main.py
```

Now answer all questions:

![img/how_to_png.png](img/how_to_png.png)

If you worked with different hourly rates during the period, run the program with a different hourly rate for each period.
For example: you worked 20 hours, from 01.09.2020 to 31.01.2020. And then you worked 25 hours.
Run the program twice, with these inputs.

If you don't know which WorkPackage/"Arbeitspaket" is you main one. Please ask.

**Git Logs**

If you worked with Git Repos, you can add all the git logs as your Remark/summary.
Create an empty folder and put all your git log files in there.
To get the files run this, in every git repo you have worked in: 

`git log --all --pretty=format:'%ai,%s' --author=GitName > log.csv`
(instead of GitName use your Git username)

Now move all log.csv into one folder. And specify the folder while the program is running:

![](./img/Screen%20Shot%202021-11-30%20at%2015.40.42.png)

## AWS Export - Extra

Open the aws excel sheet where you want to insert the time tracking. 
Open also the correct spreadsheet. Click in a writable cell!
Important...Dont close excel. it needs to be open...
Then just start the application! 
