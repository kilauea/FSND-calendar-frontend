FSND-calendar-frontend
----------------------

## Introduction

Frontend application for the Capstone project, Udacity Full Stack Nano Degree

FSND-calendar-frontend is a single page web application that displays the calendar informacion comming from the backend.

The front en allows to login, using Auth0, and send the JWT token with the backend to manage the RBAC access to the APIs.

When logged-in, the user can see his own permissions by clicking in the user name on the top right corner.

A non-recurrent task can be dragged and dropped in a new day to change the task day.

A task can be edited by double clicking on it, or by clicking the "E" button after clinking the task.

## Third Party authentication

We are using as third party authentication the Auth0 app and APIs.

### Setup Auth0

1. Create a new Auth0 Account
2. Select a unique tenant domain
3. Create a new, single page web application, CalendarService

![CalendarService](images/CalendarService1.png?raw=true)

Set the proper URLs for the "Allowed Callback URLs" and "Allowed Logout URLs" to allow the calendar front

![CalendarService](images/CalendarService2.png?raw=true)

4. Create a new API, Calendar
    - in API Settings:
        - Enable RBAC
        - Enable Add Permissions in the Access Token
5. Create new API permissions:
    - `delete:calendars`
    - `delete:tasks`
    - `get:calendars`
    - `get:tasks`
    - `patch:calendars`
    - `patch:tasks`
    - `post:calendars`
    - `post:task`
6. Create new roles for:
    - CalendarAdmin
        - can perform all actions
    - CalendarManager
        - can `delete:tasks`, `get:calendars`, `get:tasks`, `patch:tasks`, `post:tasks`
    - CalendarUser
        - can `get:calendars`, `get:tasks`

## Local development

### Installing Dependencies

#### Python 3.7

Follow instructions to install the latest version of python for your platform in the [python docs](https://docs.python.org/3/using/unix.html#getting-and-installing-the-latest-version-of-python)

#### Virtual Enviornment

We recommend working within a virtual environment whenever using Python for projects. This keeps your dependencies for each project separate and organaized. Instructions for setting up a virual enviornment for your platform can be found in the [python docs](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)

#### PIP Dependencies

Once you have your virtual environment setup and running, install dependencies by using the `requirements.txt` file running:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

This will install all of the required packages we selected within the `requirements.txt` file into the virtual environment.

### Running the application

To run the application execute the following command, using the provided run.py file:

```bash
source venv/bin/activate
python run.py
```

## Heroku deplyoment

The frontend application can be deployed to Heroku following the next steps.

### Create Heroku app

To create the application, calendar-frontend-acv, run the following command:

```
% heroku create calendar-frontend-acv
Creating ⬢ calendar-frontend-acv... done
https://calendar-frontend-acv.herokuapp.com/ | https://git.heroku.com/calendar-frontend-acv.git
```

### Add git remote for Heroku to local repository

Now we need to add a git remote to the Heroku Git:

```
% git remote add heroku https://git.heroku.com/calendar-frontend-acv.git
```

### Setup required environment

* Open the settings in the Heroku app website.
* Reveal Config Vars.
* Add the FLASK_ENV variable.

![Config Vars](images/Heroku_Config_Vars_frontend.png?raw=true)

### Push the application

To actually deploy the application we have to push it into the Heroku Git. We can use the script herokuDeployment.sh

```
% ./herokuDeployment.sh
```

### Test the application

We can check the application openning the following url: [https://dashboard.heroku.com/apps/calendar-frontend-acv](https://dashboard.heroku.com/apps/calendar-frontend-acv)
