# Cnddh-human-rights Brasil site
This application was created for Human Rights Center in Brazil for reporting violations against people that live in streets. is running in production on [http://www.cnddh.org.br](http://www.cnddh.org.br).

1. How do I get set up? Set up Install python 2.7 and Create a virtualenv:
[See here how to](http://python-guide-pt-br.readthedocs.io/en/latest/dev/virtualenvs/)

2. Install all requeriments to use:
	```
	user@server:~$ pip install -r requirements.txt
	```

3.  Install mysql and some related libs:
    ```
	user@server:~$ sudo apt-get install mysql-server mysql-client python-mysqldb libmysqlclient-dev python-dev
	```
3. Create a database on mysql:
	Step 1: Login to MySQL ( you will need an account )
    ```
    user@server:~$ mysql -u mysql_user -p
    ```
	Step 2: Create the Database
	```
	mysql > create database cnddh_db;
	```
	Step 3: Verify that it’s there
	```
	mysql > show databases;
	```
	Step 4: Create the User
	```
	mysql > create user cnddh_u;
	```
	Step 5: Grant privileges while assigning the password
	```
	mysql > grant all privileges on cnddh_db.* to cnddh_u@localhost identified by "password";
	mysql > flush privileges;
	```

4. hange the string DATABASE_URI on config.py editing for mysql://[user]:[password]localhost/[name fo database] After that just type:
    ```
	user@server:~$ python create_tables.py
	```
5. Just fun!
    ```
	user@server:~$ python runserver.py
	```
6. You access in any browser on [http://127.0.0.1:5000](http://127.0.0.1:5000). Log in using user/password adm/xpto123456 and test

7. Deployment instructions: If you are using mercurial: type hg archive [local], zip and copy to server.

8. Contribution guidelines: Create responsive layout for mobile and tablets, Update semantic Ui and reports. Update Semantic UI. Help us!!

9. Who do I talk to? Repo owner or admin dedeco@gmail.com ou andre@sousaaraujoti.com.br

## Instalation

### Linux
For install mysql need some libs:

sudo apt-get install mysql-server
sudo apt-get install libmysqlclient-dev

