# Instructions of installing the website running on your machine. 

*Add information if this is compatible only with Linux or also on Windows file system*
*Maybe include information about flask systems. probably later on or in a documentation file for curious people.*

Use the following commands in the directory that you want to have the files:

```
git clone https://github.com/TheNushu/home_finding.git
cd home_finding
source venv/bin/active
```
Now you should be in a virtual environment, fact suggested by `(venv)` appearing before your username in the following format:
```
(venv) username[...]
```
In the virtual environment, you can run the app without worrying about dependencies:
```
python3 app.py
```
This should start a server for the app website, usually with the address at: http://127.0.0.1:5000, but you will see in your terminal if it is a different address.

In order to interact with the website, open a web browser and go to the address mentioned earlier.

To close the server of the website, press `CTRL+C`.
To close the virtual environment, write `exit` command. 

