# FSND-calendar-frontend
Frontend application for the Capstone project, Udacity Full Stack Nano Degree

# Heroku deplyoment

The frontend application can be deployed to Heroku following the next steps.

## Create Heroku app

To create the application, calendar-frontend-acv, run the following command:

```
% heroku create calendar-frontend-acv
Creating ⬢ calendar-frontend-acv... done
https://calendar-frontend-acv.herokuapp.com/ | https://git.heroku.com/calendar-frontend-acv.git
```
## Add git remote for Heroku to local repository

Now we need to add a git remote to the Heroku Git:

```
% git remote add heroku https://git.heroku.com/calendar-frontend-acv.git
```

## Push the application

To actually deploy the application we have to push it into the Heroku Git. We can use the script herokuDeployment.sh

```
% ./herokuDeployment.sh
```

## Set the API backend url

We need to setup an environment variable in Heroku for the application to know the backend url

API_URL = https://calendar-backend-acv.herokuapp.com/

## Test the application

We can run the following curl command to test if the application is running.
