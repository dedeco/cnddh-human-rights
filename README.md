# cnddh-human-rights
This application was created for Human Rights Center in Brazil for reporting violations against people that live in streets

* How do I get set up? Set up Install python 2.7. Create a virtualenv. After you need install the following packages: Flask, MySQL-python, SQLAlchemy, WTForms.

* Database configuration:  Create a database on mysql, change the string DATABASE_URI on config.py editing for mysql://[user]:[password]localhost/[name fo database]' After that just type python create_tables.py on command line.

* Configuration: Just type python runserver.py on command line.

* Dependencies: Flask-Login, Flask-SQLAlchemy, Flask-Uploads and WTForms-Components.

* How to run tests: Log in using user/password adm/xpto123456 and test

* Deployment instructions: If you are using mercurial: type hg archive [local], zip and copy to server. 

* Contribution guidelines: Create responsive layout for mobile and tablets, Update semantic Ui and reports

* Who do I talk to? Repo owner or admin dedeco@gmail.com ou andre@sousaaraujoti.com.br



## Instalation

### Linux
For install mysql need some libs:

sudo apt-get install mysql-server
sudo apt-get install libmysqlclient-dev
