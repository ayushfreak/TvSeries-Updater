# Tv Series Updater

It enables the users to keep a track of all their favorite seasons and their latest episodes’ airtime by getting updates on their registered e-mail id.

## Features!

  * Verification of the email addresses entered as Input
  * Details of users stored in the database making retrival easy in future
  * List of Tv series can be Updated as per requirement in future.
  * Email service to keep the users updated with thier favourite shows

## Requirements
* Python 3.3 and up
* Mysql installed on the local machine along with credentials to make a connection
* Email Address and its password
## Installation
```
$ python3 script.py -h
$ python3 script.py <email_address> <password> <mysql user> <mysql password>
```

## Describtion
* The above email address and password are of the sender
* Above positional arguments can be entered without quotes
* If mysql password or any of the fields are none just type ""
* If you want to update the host, will have to do it manuall by opening the script   and edit line 232
* If you want to use service other than gmail you will have to update host and port in smtplib.SMTP on line 211
* Although database on local machine stores data of all the users entered since the script was run for the first time, but mail will be send to only those users whose mail addresses are entered while running the script.

## Sample inputs and outputs
### Running the script for the first time
![screenshots](https://github.com/ayushfreak/TvSeries-Updater/blob/master/screenshots/terminal1.png)
### Email Output
![screenshots](https://github.com/ayushfreak/TvSeries-Updater/blob/master/screenshots/first.png)
### Running the script for the second time while also updating an existing user
![screenshots](https://github.com/ayushfreak/TvSeries-Updater/blob/master/screenshots/terminal2.png)
### Email Output
![screenshots](https://github.com/ayushfreak/TvSeries-Updater/blob/master/screenshots/second.png)
