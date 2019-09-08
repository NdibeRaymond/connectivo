# connectivo
this web app is an attempt to build a fortnox client

## how to begin testing this app
* clone the repository
* cd into the project root directory
* install the dependencies `pip install -r requirements.txt`
* postgresql on your local machine and follow the setup wizard
* create a new user and database in postgres
* modify the settings.py to add the dabase and database user credentials to the DATABASE section
* run `python manage.py makemigrations fortnox` and `python manage.py migrate` to handle the required db migrations
* run `python manage.py runserver` to start the server

*please do not mind the size of the requirements.txt. most modules there are unneccessary but are left as a precautionary step incase other modules depend on them*
