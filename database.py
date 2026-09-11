import os, json
import sqlite3
from pathlib import Path
from datetime import datetime
DB_PATH=Path(os.getenv('GRIP_DB_PATH','grip.db')); UPLOAD_DIR=Path(os.getenv('GRIP_UPLOAD_DIR','uploads')); UPLOAD_DIR.mkdir(exist_ok=True)
def connect():
    c=sqlite3.connect(DB_PATH,check_same_thread=False); c.row_factory=sqlite3.Row; return c
def init_db():
    with connect() as c: c.executescript('''CREATE TABLE IF NOT EXISTS reports(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT,category TEXT,location TEXT,description TEXT,image_path TEXT,ai_analysis TEXT,status TEXT DEFAULT 'Reported',created_at TEXT); CREATE TABLE IF NOT EXISTS comments(id INTEGER PRIMARY KEY AUTOINCREMENT,report_id INTEGER,author TEXT,comment TEXT,created_at TEXT,FOREIGN KEY(report_id) REFERENCES reports(id));''')
def seed_demo_data():
    with connect() as c:
        if c.execute('SELECT COUNT(*) FROM reports').fetchone()[0]: return
        now=datetime.now().strftime('%Y-%m-%d %H:%M')
        samples=[('Waste dumped beside a stream','Waste','Skardu, Gilgit-Baltistan','Mixed household waste has been observed accumulating near a stream used by nearby communities.','Verified'),('Blocked drainage channel after heavy rain','Water','Gilgit, Gilgit-Baltistan','A local drainage channel is blocked by debris, increasing the risk of standing water and overflow.','Action Required'),('Open burning near residential area','Air','Hunza, Gilgit-Baltistan','Smoke from open burning was reported close to a residential area.','Reported')]
        for title,cat,loc,desc,status in samples:
            ai={'summary':desc,'priority':'Medium','possible_causes':['Improper disposal or insufficient maintenance'],'next_actions':['Verify the location','Document evidence','Refer to an appropriate local organization'],'category':cat}
            c.execute('INSERT INTO reports(title,category,location,description,ai_analysis,status,created_at) VALUES (?,?,?,?,?,?,?)',(title,cat,loc,desc,json.dumps(ai),status,now))
def save_image(b,mime='image/jpeg'):
    ext={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp'}.get(mime,'.jpg'); p=UPLOAD_DIR/f'report_{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}{ext}'; p.write_bytes(b); return str(p)
def create_report(title,category,location,description,image_bytes=None,ai_analysis=None):
    path=save_image(image_bytes) if image_bytes else None
    with connect() as c:
        cur=c.execute('INSERT INTO reports(title,category,location,description,image_path,ai_analysis,status,created_at) VALUES (?,?,?,?,?,?,?,?)',(title,category,location,description,path,json.dumps(ai_analysis or {}), 'Reported',datetime.now().strftime('%Y-%m-%d %H:%M'))); return cur.lastrowid
def list_reports():
    with connect() as c: rows=c.execute('SELECT * FROM reports ORDER BY id DESC').fetchall()
    out=[]
    for r in rows:
        d=dict(r); d['ai_analysis']=json.loads(d['ai_analysis'] or '{}'); out.append(d)
    return out
def get_report(rid):
    with connect() as c: r=c.execute('SELECT * FROM reports WHERE id=?',(rid,)).fetchone()
    if not r:return None
    d=dict(r); d['ai_analysis']=json.loads(d['ai_analysis'] or '{}'); return d
def update_status(rid,status):
    with connect() as c:c.execute('UPDATE reports SET status=? WHERE id=?',(status,rid))
def add_comment(rid,author,comment):
    with connect() as c:c.execute('INSERT INTO comments(report_id,author,comment,created_at) VALUES (?,?,?,?)',(rid,author,comment,datetime.now().strftime('%Y-%m-%d %H:%M')))
def list_comments(rid):
    with connect() as c:return [dict(r) for r in c.execute('SELECT * FROM comments WHERE report_id=? ORDER BY id ASC',(rid,)).fetchall()]
