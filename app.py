
from flask import Flask, render_template, request, redirect, url_for, session
import ibm_db
import json
import requests
import os
import ibm_boto3
from ibm_botocore.client import Config, ClientError
import webbrowser
import re
import textblob
from textblob import TextBlob
import nltk


app=Flask(__name__)
conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=ea286ace-86c7-4d5b-8580-3fbfa46b1c66.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=31505;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=bqv21717;PWD=cFPxAGvqN8Tsxwai",'','')
print(conn)



@app.route("/home")
def Home():
        return render_template("home.html")


@app.route('/')
@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/grammarcheck')
def grammarcheck():
    return render_template('grammarcheck.html')


@app.route('/login1', methods=["POST"])
def login1():
    
    USERNAME = request.form['username']
    PASSWORD = request.form['password']
    sql = "SELECT * FROM SIGNUP WHERE USERNAME = ? AND PASSWORD = ?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, USERNAME)
    ibm_db.bind_param(stmt, 2, PASSWORD)
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    print(account)
            
    if account:
        return render_template("home.html",msg = "Logged in successfully!")
    else:
        return render_template('login.html', msg= "Incorrect username / Password !")

@app.route('/register1', methods=['POST'])
def register1():
    msg=' '
    
    USERNAME = request.form['username']
    EMAIL = request.form ["email"]
    PASSWORD = request. form[ "password" ]
    sql ="SELECT * FROM SIGNUP WHERE USERNAME=? AND PASSWORD=? "
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, USERNAME)
    ibm_db.bind_param(stmt, 2, PASSWORD)
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
        
    if account:
        msg = 'Account already exists!'
        return render_template("login.html",msg=msg)
    elif not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', EMAIL):
        msg = ' Invalid email address! '
        return render_template("register.html",msg=msg)
    elif not re.match(r'[A-Za-z0-9]+', USERNAME) :
        msg ='username must contain only characters and numbers!'
        return render_template("register.html",msg=msg)
    else:
        sql2 = "SELECT count(*) FROM SIGNUP"
        stmt2 = ibm_db.prepare(conn, sql2)
        ibm_db.execute(stmt2)
        length = ibm_db.fetch_assoc(stmt2)
        print(length)
        insert_sql = "INSERT INTO SIGNUP VALUES(?,?,?,?)"
        prep_stmt = ibm_db.prepare(conn, insert_sql)
        ibm_db.bind_param(prep_stmt, 1, length[ '1']+1)
        ibm_db.bind_param(prep_stmt, 2, USERNAME)
        ibm_db.bind_param(prep_stmt, 3, EMAIL)
        ibm_db.bind_param(prep_stmt, 4, PASSWORD)
        ibm_db.execute(prep_stmt)
        msg = 'You have successfully registered !'
        return render_template("login.html", msg=msg)
    


@app.route('/grammarcheck', methods=['POST'])
def grammarCheck1():

    text = request.form[ 'text']
    print(text)
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    if sentiment==0.0:
        sentiment='15.020'
    else:
        sentiment
    noun_phrases = blob.noun_phrases
    text_noun_phrases = "\n".join(noun_phrases)
    print(text_noun_phrases)
    print(blob)
    print(sentiment)
    print(noun_phrases)
        
    insert_sql = "INSERT INTO GRAMMAR VALUES (?,?,?,?)"
    prep_stmt = ibm_db.prepare(conn, insert_sql)
    ibm_db.bind_param(prep_stmt, 1, text)
    ibm_db.bind_param(prep_stmt, 2, blob)
    print("0")
    ibm_db.bind_param(prep_stmt, 3, sentiment)
    print("1")
    ibm_db.bind_param(prep_stmt, 4, noun_phrases)
    print("2")
    ibm_db.execute(prep_stmt)
    return render_template('grammarcheck.html', sentiment=sentiment,noun_phrases=noun_phrases)
    



@app.route('/spellchecker', methods=['POST','GET'])
def Spelling():
        if request.method == 'POST':
            fieldvalues = request.form[ 'fieldvalues']
            url = "https://jspell-checker.p.rapidapi.com/check"
            payload = {
                "language":"enUS",
                "fieldvalues":fieldvalues,
                "config": {
                    "forceUpperCase": False,
                    "ignoreIrregularCaps": False,
                    "ignoreFirstCaps": True,
                    "ignoreNumbers": True,
                    "ignoreUpper": False,
                    "ignoreDouble": False,
                    "ignoreWordsWithNumbers": True,
                }
            }

        
            headers = {
                "content-type": "application/json",
                "X-RapidAPI-Key":"ad8dd9e205msh1b46ee7d2f5246fp145c0bjsn4f9d4d717193",
                "X-RapidAPI-Host": "jspell-checker.p.rapidapi.com"
            }
            response = requests.request("POST", url, json=payload, headers=headers)
            response_dict = response.json()
            print(response_dict)
            
            spelling_error_count = response_dict['spellingErrorCount'] 
        
            if spelling_error_count == 0:
                 return render_template("spellchecker.html",fieldvalues=fieldvalues,speLling_error_count=spelling_error_count)
            else:
                elements = response_dict['elements' ]
                error_list = []
                for element in elements:
                    error = element['errors'][0]
                    word = error['word']
                    position = error['position' ]
                    suggestions = error[ 'suggestions']
                    error_list.append((word, position, suggestions) )
          
            insert_sql = "INSERT INTO SPELLINGCHECKER VALUES (?,?,?,?)"
            stmt = ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(stmt, 1, word)
            ibm_db.bind_param(stmt, 2, spelling_error_count)
            ibm_db.bind_param(stmt, 3, position)
            ibm_db.bind_param(stmt, 4, suggestions)
            ibm_db.execute(stmt)
            
            return render_template ( "spellchecker.html",response_dict=response_dict)
        else: 
            return render_template("spellchecker.html")



@app.route('/summarize', methods=['POST','GET'])
def summarise():
        
        if request.method == 'POST':
            text = request.form['text']
            num_sentences = int(request.form['num_sentences'])
            
            url = "https://gpt-summarization.p.rapidapi.com/summarize"
            payload = {
                    "text": text,
                    "num_sentences": num_sentences
            }
            headers = {
                    "content-type": "application/json",
                    "X-RapidAPI-Key":"ad8dd9e205msh1b46ee7d2f5246fp145c0bjsn4f9d4d717193",
                    "X-RapidAPI-Host":"gpt-summarization.p.rapidapi.com"
            }
            response = requests.post(url, json=payload, headers=headers)
            summary = response.json()
            insert_sql = "INSERT INTO SUMMARY VALUES (?,?,?)"
            stmt = ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(stmt, 1, text)
            ibm_db.bind_param(stmt, 2, num_sentences)
            ibm_db.bind_param(stmt, 3, summary)
            ibm_db.execute(stmt)
            return render_template("summarize.html", summary=summary )
        return render_template("summarize.html")



@app.route('/logout' )

def logout():
     session.pop('loggedin' ,None)
     session.pop( 'USERID' ,None)
     return render_template('login.html')


if __name__ == "__main__":
    app.run(debug = True, port = 5000)
