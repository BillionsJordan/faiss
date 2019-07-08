from jsonschema import validate, ValidationError
from flask import Blueprint, jsonify, request, json, render_template
from werkzeug.exceptions import BadRequest
from faiss_index import FaissIndex
import faiss
import numpy as np
import MySQLdb
import regex
import os
import multiprocessing
import ast
import time
np.set_printoptions(suppress=True)
try:
    import uwsgi
except ImportError:
    print('Failed to load python module uwsgi')
    print('Periodic faiss index updates isn\'t enabled')
    uwsgi = None

# Set blueprint
create_db = Blueprint("create_db", __name__, template_folder="html", static_folder="static") # type:Blueprint
@create_db.route("/faiss/create_db",methods=["GET","POST"])
def create_db_new():
    if request.method == "POST":
        # get form data
        db_dic = {
            "database": request.form["database"]
        }
        db_name = db_dic['database']
        # This connect to mysql on my computer.If you want to deploy to mysql on the server,change them please
        db = MySQLdb.connect('192.168.99.1', port=3306, user='root', password='12345678', charset='utf8' )
        cursor = db.cursor()
        try:
            cursor.execute('CREATE SCHEMA %s' %db_name)
        except Exception as e:
            return '%s has exist'%db_name
        try:
            db2=MySQLdb.connect('192.168.99.1', port=3306, user='root', password='12345678', db=db_name, charset='utf8')
        except Exception as e:
            cursor.execute('DROP SCHEMA %s' % db_name)
            return 'please input english name!'
        cursor2=db2.cursor()
        # note:id stored as VARCHAR, feature stored as BLOB!!
        sql='CREATE TABLE feature(`mysql_id` INT NOT NULL AUTO_INCREMENT,`id` VARCHAR(45) NOT NULL,`feature` BLOB NOT NULL,PRIMARY KEY (`mysql_id`))'
        cursor2.execute(sql)
        db2.commit()
        return 'create succeed!'
    # gain form
    return render_template("create_db.html")

@create_db.route("/faiss/insert_f",methods=["GET","POST"])
def insert_f_new():
    if request.method == "POST":
        try:
            # get form data
            # This code currently only supports 128-dimensional vectors. If you want to support more, please modify the following dic[key]==128
            db_dic = {
                "database": request.form["database"],
                "vectors" : request.form['vectors']
            }
            db_name = db_dic['database']
            str1 = db_dic['vectors']
            db = MySQLdb.connect('192.168.99.1', port=3306, user='root', password='12345678', db = db_name, charset='utf8')
            cursor = db.cursor()
            try:
                # string to dictionary
                dic = ast.literal_eval(str1)
            except:
                return 'too much data!'
            for key in dic:
                if(len(dic[key])==128):
                    cursor.execute("insert into feature(id,feature) values(%s,%s)",([key],[np.array(dic[key])]))
            db.commit()
            return 'insert succeed!'
        except:
            return 'incorrect input!'
    return render_template("insert_feature.html")

@create_db.route("/faiss/rebuild_index",methods=["GET","POST"])
def rebuild_index_new():
    if request.method == "POST":
        # gain form data
        db_dic = {
            "database": request.form["database"]
        }
        db_name = db_dic['database']
        try:
            db = MySQLdb.connect('192.168.99.1', port=3306, user='root', password='12345678', db=db_name, charset='utf8' )
        except Exception as e:
            return 'no database called %s'%db_name
        cursor = db.cursor()
        # This code currently only supports 128-dimensional vectors. If you want to support more, please modify d=128 below.
        d = 128
        path = './%s' % str(db_name)
        isExists = os.path.exists(path)
        # build a new index if no save before
        if isExists == False:
            os.mkdir(path)
            index = faiss.IndexFlatL2(d)
            index_with_ids = faiss.IndexIDMap(index)
        # read index saved before
        else:
            index_with_ids = faiss.read_index(path+'/index')
        isExists2 = os.path.exists(path+'/id_end.txt')
        # find the last id of mysql that rebuild index last time
        if isExists2:
            with open(path+'/id_end.txt','r')as f:
                end = int(f.read())
        # if id dosent exit,set 0
        else:
            end = 0
        try:
            # fetch data from mysql:stream to list
            xb = []
            cursor.execute('select * from feature where mysql_id > %s',([end]))
            feature4 = cursor.fetchall()
            for i in range(len(feature4)):
                feature5 = feature4[i][2].decode()
                array2 = feature5.split()
                feature6 = []
                for c in array2:
                    c = regex.findall('[0-9.]+', c)
                    if c == []:
                        continue
                    feature6.append(c[0])
                xb.append(feature6)
            # The faiss add index requires data must be array and float32
            xb = np.array(xb).astype('float32')
            ids1 = (np.arange(end,end+len(feature4)) + 1).astype('int')
            index_with_ids.add_with_ids(xb, ids1)
        except Exception as e:
            return 'no data increased in %s,no need to rebuild index'%(db_name)
        # save index
        faiss.write_index(index_with_ids,path+'/index')
        # save id
        with open(path+'/id_end.txt','w')as f:
            f.write(str(end+len(feature4)))
        return 'rebuild succeed!'
    # gain form
    return render_template("rebuild_index.html")

@create_db.route("/faiss/search",methods=["GET","POST"])
def search_new():
    if request.method == "POST":
        try:
            # get form data
            db_dic = {
                "database": request.form["database"],
                "k":request.form["k"],
                "vectors":request.form["vectors"]
            }
            db_name = db_dic['database']
            db_vectors = db_dic['vectors']
            k = int(db_dic["k"])
            try:
                # try to get index
                index=faiss.read_index('%s/index' %str(db_name))
            except Exception:
                return 'there is no index yet!'
            # Get the input vector:string to list
            vectors = []
            feature3 = []
            c = regex.findall('[0-9.]+', db_vectors)
            for i in range(len(c)):
                if c[i] != []:
                    feature3.append(float(c[i]))
                if (i + 1) % 128 == 0:
                    vectors.append(feature3)
                    feature3 = []
            ids2 = (np.arange(len(vectors)) + 1).astype('int')
            id_vector = dict(zip(ids2,vectors))
            # get search research results
            create_db.create_db = FaissIndex(index, id_vector, db_name)
            results = create_db.create_db.search_by_vectors(vectors, k)
            return jsonify(results)
        except Exception as e:
            return 'incorrect input!'
    return render_template("search.html")

