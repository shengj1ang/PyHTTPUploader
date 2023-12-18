from flask import Flask, request, jsonify, session
import hashlib, random, os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 设置秘钥
enable_session=True

def md5(fcontent):
    return str(hashlib.md5(fcontent).hexdigest())
   
   
   
@app.route('/')
def hello_world():
   return 'Invalid Requests<br>Program Works Properly.'

@app.route('/upload', methods=["GET"])
def web_page_upload():
   return('''<html>
<head>
  <title>File Upload</title>
</head>
<body>
    <form action="/upload" method="POST" enctype="multipart/form-data">
        <input type="file" name="file"  />
        <input type="submit" value="提交" />
    </form>
</body>
</html>''')


@app.route("/upload", methods=["POST"])
def save_file():
    data = request.files
    #print("start...")
    #print(type(data))
    #print(data)
    file = data['file']
    print(file.filename)
    #print(request.headers)
    file.save("files/"+file.filename)
    #print("end...")
    return('''<html>
<head>
  <title>File Upload</title>
</head>
<body>
    <form action="/upload" method="POST" enctype="multipart/form-data">
        <input type="file" name="file"  />
        <input type="submit" value="提交" />
    </form>
<h1>上传成功</h1>
</body>
</html>''')


@app.route("/advanced_upload", methods=["GET","POST"])
def advanced_upload():
    session_id=session.get('session_id', '') 
    if session_id=="":
        session["session_id"]=str(random.randint(10000,99999))
    session_id=session.get('session_id', '') 
    if request.method == 'GET':
        return jsonify({"result":"suc","detail":"Here's the advaced_upload path, session created. To upload file(s), POST method should be used.", "session_id":session_id})
    if request.form["md5"]=="complete":             #md5值为“complete”时，合并文件。
        try:
            filename=f"files/{session_id}/{request.form['filename']}"    #文件名
            chunk = 1                                  # 分片序号
            with open(filename, 'wb') as target_file:  # 创建新文件
                while True:
                    try:
                        chunk_file = filename+f".{chunk}.chunk"
                        source_file = open(chunk_file, 'rb')                    # 按序打开每个分片
                        target_file.write(source_file.read())                 # 读取分片内容写入新文件
                        source_file.close()
                        os.remove(chunk_file)                     # 删除该分片，节约空间
                    except IOError:
                        break
                    chunk += 1  
            return jsonify({"result":"suc","detail":f"The file [{session_id}/{filename}] has been combined successfully."})
        except Exception as ex:
            print(ex)
            return jsonify({"result":"fail","detail":f"The file [{session_id}/{filename}] met an error: {str(ex)}"})
    else:
        try:
            data = request.files['chunk_file'].read()   #收到的二进制切片文件数据
            
            if data is None:
                return jsonify({"result":"fail","detail":f"The chunk file [{session_id}/{filename}] Not Received"})
            
            data_md5=hashlib.md5(data).hexdigest() #收到的二进制切片文件MD5
            filename=f"files/{session_id}/{request.form['filename']}"     #文件名
            part=request.form["part"]              #分片序号
            origin_md5=request.form["md5"]         #客户端计算的MD5

            #print(len(data))
            if data_md5==origin_md5:
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                if part=="0":
                    with open(filename,"wb") as f:
                        f.write(data)
                    return jsonify({"result":"suc","detail":f"The small file [{session_id}/{filename}] uploaded"})
                else:
                    with open(filename+f".{part}.chunk","wb") as f:
                        f.write(data)
                    return jsonify({"result":"suc","detail":f"The chunk file [{session_id}/{filename}], part[{part}]"})
            else:
                return jsonify({"result":"fail","detail":f"The (chunk) file [{session_id}/{filename}] DifferentMD5"})
        except Exception as ex:
            print(ex)
            return jsonify({"result":"fail","detail":f"The chunk file [{session_id}/{filename}] met an error: {str(ex)}"})
    
    
if __name__ == '__main__':
   #app.run(port=37000,  debug=True)
   app.run('0.0.0.0',port=65533, debug=False)
