import datetime

from flask import Blueprint, Flask
from flask import render_template, request, redirect, url_for, jsonify, session, g, session

from . import db

bp = Blueprint("pim","pim",url_prefix="")

@bp.route("/")
def home_page():
  return render_template("home_page.html")
  
@bp.before_request
def before_request():
  if 'usr_id' in session :
    user=session['usr_id']
  else :
    user=None
  g.user = user
  
@bp.route("/login", methods = ["GET","POST"] )
def login() :
  if request.method == "POST" :
    conn = db.get_db()
    cursor = conn.cursor()
    usr_name = request.form.get('usr_name')
    password = request.form.get('pass')
    cursor.execute("SELECT * FROM usr WHERE username = ? ;",[usr_name])
    usr = cursor.fetchone()
    if usr == None :
      return render_template("login.html",error=201)
    usr_id, username, pass_wrd = usr
    if password == pass_wrd :
      session['usr_id'] = usr_id
      return redirect(url_for("pim.profile"),302)
    else :
      return render_template("login.html",error=202)
  return render_template("login.html")

@bp.route("/profile/logout")
def logout():
  session.pop('usr_id',None)
  return redirect(url_for("pim.home_page"),302)

@bp.route("/register", methods=["GET","POST"])
def register():
  if request.method == "POST" :
    conn = db.get_db()
    cursor = conn.cursor()
    new_usr = request.form.get('new_usr')
    new_pass_1 = request.form.get('new_pass_1')
    new_pass_2 = request.form.get('new_pass_2')
    cursor.execute("SELECT username FROM usr ;") 
    usr_names = cursor.fetchall()
    for names in usr_names :
      if new_usr in names :
        return render_template("register.html",error=101) 
    if not new_pass_1 == new_pass_2 :
      return render_template("register.html",error=102)
    if not len(new_pass_1) >= 8 :
      return render_template("register.html",error=103)
    else : 
      cursor.execute("INSERT INTO usr (username,pass_wrd) VALUES( ? , ? );",(new_usr,new_pass_1))
      conn.commit()
      return  redirect(url_for("pim.login"),302)
  return render_template("register.html",error=0)
  
@bp.route("/profile")
def profile():
  if not g.user :
    return render_template("login.html",error=203)
  return render_template("home_page.html")
  
@bp.route("/profile/my_notes")
def my_notes():
  if not g.user :
    return render_template("login.html",error=203)
  conn = db.get_db()
  cursor = conn.cursor()
  cursor.execute("SELECT note_id, title, created, description FROM notes WHERE note_admin = ? ;",[g.user])
  notes = cursor.fetchall()
  return render_template("my_notes.html",notes=notes)  
  
@bp.route("/profile/create_note", methods = ["GET","POST"])
def create_note():
  if not g.user :
    return render_template("login.html",error=203)
  if request.method == "POST" :
    conn = db.get_db()
    cursor = conn.cursor()
    title = request.form.get('title')
    hashtags = request.form.get('hashtags')
    description = request.form.get('description')
    now = datetime.date.today()
    datef = now.strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO notes (note_admin,title,created,description) VALUES (?,?,?,?);",(g.user,title,datef,description))
    conn.commit()
    cursor.execute("SELECT note_id FROM notes WHERE note_admin = ? AND title = ? AND description = ? ;",(g.user,title,description))
    note_id = cursor.fetchone()
    note_id = note_id[0] 
    hashtags=hashtags.split(" ")
    cursor.execute("SELECT hashtag FROM hashtags WHERE ht_admin = ? ;",[g.user])
    ht_user = []
    for x in cursor.fetchall():
      ht_user.append(x[0])
    for x in hashtags :
      if not x in ht_user : 
        cursor.execute("INSERT INTO hashtags ( ht_admin , hashtag ) VALUES ( ? , ? );",(g.user,x))
        conn.commit()
      cursor.execute("SELECT ht_id FROM hashtags WHERE hashtag = ? AND ht_admin = ? ;",(x,g.user))
      ht_id = cursor.fetchone()
      ht_id = ht_id[0]
      cursor.execute("INSERT INTO notes_ht VALUES ( ? , ? );",(note_id,ht_id))
      conn.commit()
    return  redirect(url_for("pim.my_notes"),302)
  return render_template("create_note.html",note=None)
  
@bp.route("/profile/<note_id>")
def view_note(note_id):  
  if not g.user :
    return render_template("login.html",error=203)
  conn = db.get_db()
  cursor = conn.cursor()
  cursor.execute("SELECT note_id, title, created, description  FROM notes WHERE note_admin=? AND note_id=? ;",(g.user,note_id))
  note = cursor.fetchone()
  cursor.execute("SELECT h.hashtag FROM hashtags h, notes_ht nh WHERE h.ht_admin= ? AND nh.note= ? AND h.ht_id=nh.ht ;",(g.user,note_id)) 
  hashtags=(x[0] for x in cursor.fetchall())
  return render_template("view_notes.html",note=note,hashtags=hashtags)      
  
@bp.route("/profile/<note_id>/edit_note", methods = ["GET","POST"])
def edit_note(note_id): 
  if not g.user :
    return render_template("login.html",error=203)
  conn = db.get_db()
  cursor = conn.cursor()
  if request.method == "POST" :
    edited_title = request.form.get('title')
    edited_description = request.form.get('description')
    cursor.execute("UPDATE notes SET title= ?, description= ? WHERE note_id= ? ;",(edited_title,edited_description,note_id))
    conn.commit()
    return redirect(url_for('pim.my_notes'),302)
  cursor.execute("SELECT note_id, title, description, created FROM notes WHERE note_id= ? AND note_admin= ? ;",(note_id , g.user))
  note = cursor.fetchone()     
  cursor.execute("SELECT h.hashtag FROM hashtags h, notes_ht nh WHERE h.ht_admin= ? AND nh.note= ? AND h.ht_id=nh.ht ;",(g.user,note_id))
  hashtags = (x[0] for x in cursor.fetchall())
  return render_template("create_note.html",note=note,hashtags=hashtags)
     
  
@bp.route("/profile/my_hashtags")
def my_hashtags():
  if not g.user :
    return render_template("login.html",error=203)
  conn = db.get_db()
  cursor = conn.cursor()
  cursor.execute("SELECT hashtag, ht_id FROM hashtags WHERE ht_admin = ? ;",[g.user])
  hashtags = cursor.fetchall() 
  return render_template("my_hashtags.html",hashtags=hashtags)
  
@bp.route("/profile/my_hashtags/<tag>")
def tag_search(tag):
  if not g.user :
    return render_template("login.html",error=203)
  conn = db.get_db()
  cursor = conn.cursor()
  cursor.execute("SELECT n.note_id, n.title, n.created, n.description FROM notes n, notes_ht nh WHERE nh.ht=? AND n.note_id=nh.note AND n.note_admin=? ;",(tag,g.user))
  notes = cursor.fetchall()
  return render_template("my_notes.html",notes=notes)
  

@bp.route("/profile/search",methods=["GET","POST"])
def search():
  if not g.user :
    return render_template("login.html",error=203)
  if request.method == "POST" :
    element = request.form.get('search')
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT note_id, title, created, description FROM notes WHERE note_admin = ? ;",[g.user])
    notes = cursor.fetchall()
    results=[]
    for note in notes :
      if element in note[1] or element in note[3] :
        results.append(note)
    return render_template("my_notes.html",notes=results)
  return render_template("search.html")
  
@bp.route("/profile/<note_id>/delete")
def delete_note(note_id):
  if not g.user :
    return render_template("login.html",error=203)
  conn = db.get_db()
  cursor = conn.cursor()
  cursor.execute("DELETE FROM notes WHERE note_id = ? AND note_admin = ? ;",(note_id,g.user))
  conn.commit()
  return redirect(url_for("pim.my_notes"),302)
  

