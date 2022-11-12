#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver
To run locally
    python server.py
Go to http://localhost:8111 in your browser
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os

from flask import (Flask, Response, abort, flash, g, redirect, render_template,
                   request, session)
from sqlalchemy import *
from sqlalchemy.pool import NullPool

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
genders = ['Female', 'Male', 'Non-binary', 'NA']
myprofile=dict()



# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "zj2334"
DB_PASSWORD = "1502"

DB_SERVER = "w4111project1part2db.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request
  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print ("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


def reset():
  session['genders']=genders
  session['logged_in']=False
  session['uid'] = ''
  session['signup']=dict()
  session['modifyprofile']=dict()
  myprofile=dict()

@app.route('/')
def home():
  if not session.get('logged_in'):
    reset()
    return render_template('login.html')
  else:
	  return render_template('user_main_page.html')

@app.route('/login', methods=['POST'])
def login():
  login_query="SELECT * FROM users WHERE name=(%s) AND passwd=(%s);"
  data=(request.form['username'], request.form['password'],)
  cursor=g.conn.execute(login_query,data)
  row = cursor.fetchone()
  if  row:
    reset()
    session['logged_in'] = True
    session['uid']=row['uid']
  else:
    cursor.close()
    return render_template('wrong_password.html')
  cursor.close()
  return home()

@app.route("/retry", methods=['POST'])
def retry():
	session['logged_in'] = False
	return home()

@app.route("/logout", methods=['POST'])
def logout():
	session['logged_in'] = False
	return home()

@app.route("/signuppage", methods=['POST'])
def signuppage():
	return render_template('sign_up.html')

@app.route("/myprofilepage", methods=['POST'])
def myprofilepage():
  if not session.get('logged_in'):
    return home()
  login_query="SELECT * FROM users WHERE uid=(%s);"
  data=(session['uid'],)
  cursor=g.conn.execute(login_query,data)
  row = cursor.fetchone()
  myprofile['username'] = row['name']
  myprofile['password'] = row['passwd']
  myprofile['uid']=row['uid']
  myprofile['gender'] =  row['gender']
  myprofile['self_desc']= row['self_description']
  myprofile['city']=row['city'] 
  myprofile['bday'] = row['birthday']
  myprofile['pgender']=row['p_gender']
  myprofile['pcity']=row['p_city']
  myprofile['page'] = row['p_age']
  myprofile['genders']=genders
  return render_template('my_profile_page.html',**myprofile)

@app.route("/modifymyprofilepage", methods=['POST'])
def modifymyprofilepage():
  if not session.get('logged_in'):
    return home()
  return render_template('modify_myprofile.html')


@app.route("/modifymyprofile", methods=['POST'])
def modifymyprofile():
  if not session.get('logged_in'):
    return home()
  if (len(request.form['password'])>0 and len(request.form['password'])<6):
    session['modifyprofile']['short_password'] = True
    return modifymyprofilepage()
  
  username=myprofile['username']
  if not len(request.form['username'])==0:
    username=request.form['username']
  
  password=myprofile['password']
  if not len(request.form['password'])==0:
    password=request.form['password']
  if not myprofile['username']==username or not myprofile['password']==password:
    check_query="SELECT * FROM users WHERE name=(%s) AND passwd=(%s);"
    data=(username, password,)
    cursor=g.conn.execute(check_query,data)
    row = cursor.fetchone()
    if  row:
      session['modifyprofile']['dup_name_password'] = True
      return render_template('modify_myprofile.html')
  myprofile['username']=username
  myprofile['password']=password

  if not request.form['gender']=='-1':
    myprofile['gender']=int(request.form['gender'])

  if not len(request.form['self_desc'])==0:
    myprofile['self_desc']=request.form['self_desc']

  if not len(request.form['city'])==0:
    myprofile['city']=request.form['city']

  if not len(request.form['bday'])==0:
    myprofile['bday']=request.form['bday']

  if not request.form['pgender']=='-1':
    myprofile['pgender']=int(request.form['pgender'])

  if not len(request.form['pcity'])==0:
    myprofile['pcity']=request.form['pcity']

  if not len(request.form['page'])==0:
    myprofile['page']=int(request.form['page'])
    
  signup_query="UPDATE users SET passwd=(%s), gender=(%s), name=(%s),self_description=(%s), city=(%s), birthday=(%s), p_gender=(%s),p_city=(%s),p_age=(%s) WHERE uid=(%s);"
  data= (myprofile['password'], myprofile['gender'], myprofile['username'], myprofile['self_desc'],myprofile['city'], myprofile['bday'],myprofile['pgender'], myprofile['pcity'],myprofile['page'],session['uid'],)
  g.conn.execute(signup_query,data)
  return render_template('success.html') 

@app.route("/signup", methods=['POST'])
def signup():
  reset()
  if (len(request.form['password'])<6):
    session['signup']['short_password'] = True
    return signuppage()
  if (len(request.form['username']) ==0 or len(request.form['bday'])==0):
    session['signup']['missing_input'] = True
    return signuppage()

  check_query="SELECT * FROM users WHERE name=(%s) AND passwd=(%s);"
  data=(request.form['username'], request.form['password'],)
  cursor=g.conn.execute(check_query,data)
  row = cursor.fetchone()
  if  row:
    session['signup']['dup_name_password'] = True
  else:
    check_query="SELECT max(uid)+1 as uid FROM users;"
    cursor=g.conn.execute(check_query)
    row = cursor.fetchone()
    uid=row['uid']
    page=None
    if not len(request.form['page'])==0:
      page=int(request.form['page'])
    signup_query="INSERT INTO  users VALUES ((%s),(%s),(%s),(%s),(%s),(%s),(%s),(%s),(%s),(%s));"
    data= (uid, request.form['password'], int(request.form['gender']), request.form['username'], request.form['self_desc'],request.form['city'], request.form['bday'],int(request.form['pgender']), request.form['pcity'],page)
    g.conn.execute(signup_query,data)
    return render_template('success.html')
  return render_template('sign_up.html')

@app.route("/success", methods=['POST'])
def success():
	return home()


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)


  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using
        python server.py
    Show the help text using
        python server.py --help
    """

    HOST, PORT = host, port
    print ("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  app.secret_key = "super secret key"

  run()
