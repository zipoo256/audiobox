﻿#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      nbergont
#
# Created:     12/02/2015
# Copyright:   (c) nbergont 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from flask import Flask, request, render_template, url_for, redirect, session
import json
import uuid
import hashlib
import os

CONF_FILE = 'conf.json'

app = Flask("audiobox")
app.secret_key = '7b237c9e4e47de2b27a247a3c1a7d7bc'
app.config['UPLOAD_FOLDER'] = 'static/media'

#*********** GLOBAL FUNCTIONS **************
conf = {}
def load_conf():
	global conf
	conf = json.loads(open(CONF_FILE, 'r').read())

def save_conf():
	global conf
	open(CONF_FILE, 'w').write(json.dumps(conf, indent=True))

def get_title():
	global conf
	return conf["audiobox"]["home_title"]

def getFile(id):
	global conf
	for sec in conf["sections"]:
		for file in sec["files"]:
			if file['id'] == id:
				return file
	return None
	
def genSecId():
	global conf
	id = 0
	for sec in conf["sections"]:
		if id < sec['id']:
			id = sec['id']
	return id + 1

def genFileId():
	global conf
	id = 0
	for sec in conf["sections"]:
		for file in sec["files"]:
			if id < file['id']:
				id = file['id']
	return id + 1
	
def hash_password(password):
	return hashlib.sha224(app.secret_key + password).hexdigest()

def isAdmin():
	return session['username'] == conf["audiobox"]["admin_login"]
	#return 'username' in session

def allowed_ext(filename, ext):
	return filename.rsplit('.', 1)[1].lower() in ext
		
#*********** SERVER FUNCTIONS **************
@app.route('/')
@app.route('/list')
def list_page():
	global conf
	return render_template ('list.html', sections=conf["sections"], title=get_title())


@app.route ('/play/<int:id>')
def play_page(id):
	global conf
	f = getFile(id)
	if f :
		return render_template ('play.html', file=f, title=get_title())
	return redirect('list')


@app.route('/admin')
def admin_page():
	global conf
	if isAdmin():
		return render_template ('admin.html', audiobox=conf["audiobox"], sections=conf["sections"], title=get_title())
	return redirect('login')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
	global conf
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']

		if username == conf["audiobox"]['admin_login'] and hash_password(password) == conf["audiobox"]['admin_password']:
			session['username'] = username
			return redirect('admin')
		else :
			return render_template ('error.html', msg='Wrong password or username', title=get_title())

	return render_template ('login.html', title=get_title())

@app.route('/logout')
def logout_page():
	session.pop('username', None)
	return redirect('list')
	
	
@app.route('/set_options', methods=['POST'])
def set_options_post():
	global conf
	if isAdmin() and request.method == 'POST':
		conf["audiobox"]['home_title'] = request.form['home_title']
		conf["audiobox"]['hostspot_name'] = request.form['hostspot_name']
		save_conf()
		
	return redirect('admin')


@app.route('/set_login', methods=['POST'])
def set_login_post():
	global conf
	if isAdmin() and request.method == 'POST':
		login = request.form['login']
		password1 = request.form['password1']
		password2 = request.form['password2']
		
		if password1 == password2:
			conf["audiobox"]['admin_login'] = login
			conf["audiobox"]['admin_password'] = hash_password(password1)
			conf["audiobox"]['first_launch'] = False
			save_conf()
			session.pop('username', None)
		
	return redirect('login')

@app.route ('/remove/<int:id>')
def remove_page(id):
	global conf
	if isAdmin():
		for sec in conf["sections"]:
			for file in sec["files"]:
				if id == file['id']:
					os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file['filename']))
					sec["files"].remove(file)
					save_conf()
					return redirect('admin')
	return redirect('login')
	
@app.route ('/remove_section/<int:id>')
def remove_sec_page(id):
	global conf
	if isAdmin():
		for sec in conf["sections"]:
			if id == sec['id']:
				for file in sec["files"]:
					os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file['filename']))
				conf["sections"].remove(sec)
				save_conf()
				return redirect('admin')
	return redirect('login')

	
@app.route ('/move_up/<int:id>')
def move_up_action(id):
	global conf
	if isAdmin():
		for sec in conf["sections"]:
			files = sec["files"]
			for i, file in enumerate(files):
				if file['id'] == id and i > 0:
					files[i], files[i-1] = files[i-1], files[i]
					save_conf()
					break
		return redirect('admin')
	return redirect('login')
	
@app.route ('/move_down/<int:id>')
def move_down_action(id):
	global conf
	if isAdmin():
		for sec in conf["sections"]:
			files = sec["files"]
			for i, file in enumerate(files):
				if file['id'] == id and i < len(files):
					print i
					files[i+1], files[i] = files[i], files[i+1]
					save_conf()
					break
		return redirect('admin')
	return redirect('login')
	
@app.route ('/edit/<int:id>', methods=['GET', 'POST'])
def edit_page(id):
	global conf
	if isAdmin():
		f=getFile(id)
		if request.method == 'POST':
			f['tag'] = request.form['tag']
			f['label'] = request.form['label']
			f['desc'] = request.form['description']
			save_conf()
			return redirect('admin')
		else:
			return render_template ('edit.html', file=f, title=get_title())
	return redirect('login')

@app.route('/upload')
def upload_page():
	global conf
	if isAdmin():
		return render_template ('upload.html', sections=conf["sections"], title=get_title())
	return redirect('login')

@app.route('/upload_file', methods=['POST'])
def upload_file_post():
	global conf
	if isAdmin() and request.method == 'POST':
		section = request.form['section']
		tag = request.form['tag']
		label = request.form['label']
		description = request.form['description']
		file = request.files['file']
		
		if file and allowed_ext(file.filename, ['mp3']):
			filename = uuid.uuid4().hex + '.mp3'
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			
			for sec in conf["sections"]:
				if sec['label'] == section:
					sec['files'].append({'label':label,'tag':tag,'desc':description,'filename':filename, 'type': 'audio', 'id':genFileId()})
					save_conf()
					return redirect('admin')
		
		return render_template ('error.html', msg='Wrong file type', title=get_title())

	return redirect('login')
	
@app.route('/add_section', methods=['POST'])
def add_section_post():
	global conf
	if isAdmin() and request.method == 'POST':
		label = request.form['label']
		conf['sections'].append({'label':label, 'id':genSecId(), 'files':[]})
		save_conf()
	return redirect('admin')
	
#*********** MAIN **************
if __name__ == '__main__':
	load_conf()
	app.run(debug=True, port=80)
	#app.run(debug=True, host='0.0.0.0', port=80, threaded=True)
