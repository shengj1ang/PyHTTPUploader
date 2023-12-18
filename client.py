import sys, os, time, threading, hashlib, json
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
num_thread=0
max_thread=12
session=requests.Session()
session.verify=False

def about():
    print("""
    ---PyHTTPTransfer---
    1. This program is designed to upload big files/folders to a remote server in poor network conditions by using Requests=>Flask (C/S)
    2. File/Folder can be automatically detected.
    3. One command and everything is done, retries will be applied if errors.
    4. Multiple threads, so full use of the bandwidth.
    5. An example: Server in China, Client in the UK, Full Bandwidth usage in extreme conditions.
    6. Also support small files with high speed upload
    """)
def uploader(link,payload,part_content): 
    max_retry=30
    retry=0
    global num_thread
    global session
    num_thread+=1
    while True:
        if retry>max_retry:
            num_thread-=1
            return("MaxRetryReached")
        else:
            try:
                r = session.post(link,data=payload,files= {'chunk_file': part_content})
                resp=r.content.decode()
                if retry>0:
                    print(f'[Retry: {str(retry)}]{resp}')
                else:
                    print(resp)
                    pass
                parsed_resp = json.loads(resp)
                if parsed_resp["result"]=="suc":
                    num_thread-=1
                    print(f"{parsed_resp['detail']}")
                    return("True")
            except Exception as ex:
                print(ex)
                retry+=1
def file_split(link,full_path, save_path):
    size = 1024 * 1000 * 10  # 10MB
    threads = []
    global num_thread
    global max_thread
    global session
    file_size = os.path.getsize(full_path)  # Size in bytes
    if file_size<=size: #For Small Files
        with open(full_path, "rb") as reader:
            file_content=reader.read()
        f_md5=hashlib.md5(file_content).hexdigest()  
        print(f"[{full_path}-SmallFile]   [{file_size/1024/1000}MB]     MD5:{f_md5}")
        payload={"filename":save_path, "part":"0", "md5":f_md5}
        #print(payload)
        while True:
            #print(num_thread)
            if num_thread>=max_thread:
            
                time.sleep(0.5)
            else:    
                t = threading.Thread(target=uploader, args=(link,payload,file_content ))
                threads.append(t)
                t.start()
                time.sleep(0.1)
                break
    else:
        with open(full_path, "rb") as reader:
            part = 1
            while True:
                part_content = reader.read(size)
                if not part_content:
                
                    print(f"[File {full_path}] split done.")
                    
                    for t in threads:
                        t.join()
                    #while num_thread>0:
                    #    print(f"Waiting for all thread complete，thread remain: {str(num_thread)}")
                    #    time.sleep(3)
                    print(f"[{save_path}] All part uploaded, start to combine chuncks.")
                    payload={"filename":save_path,  "md5":"complete"}
                    r = session.post(link,data=payload)
                    print(r.content.decode())
                    break
                #with open(f"bigfile_part{part}","wb") as writer:
                #    writer.write(part_content)
                
                f_md5=hashlib.md5(part_content).hexdigest()
                
                print(f"[{full_path}-Part-{part}]   [{size*part/1024/1000}MB]     MD5:{f_md5}")
                payload={"filename":save_path, "part":str(part), "md5":f_md5}
                #print(payload)
                while True:
                    #print(num_thread)
                    if num_thread>=max_thread:
                    
                        time.sleep(0.5)
                    else:    
                        t = threading.Thread(target=uploader, args=(link,payload,part_content ))
                        threads.append(t)
                        t.start()
                        time.sleep(0.1)
                        break
                part+=1

       
base_url="https://upload.example.com:60000/65533"
session.get(f"{base_url}/advanced_upload")
if len(sys.argv)<2:
    print("You should use [client.py/client.exe] [file/folder]\nUse [client.py/client.exe] --about to get details")
    sys.exit()
path=sys.argv[1]
if path=="--about":
    about()
    sys.exit()
if not (os.path.isfile(path) or os.path.isdir(path)):
    print ("The path is neither a file nor a directory.\nUse [client.py/client.exe] --about to get details")
    sys.exit()
if not os.path.exists(path):
    print ("File or directory does not exist.")
    sys.exit()
# If it's a file
if os.path.isfile(path):
    input(f"Do you mean: Upload File [{path}] to [{os.path.basename(path)}]")
    file_split(f"{base_url}/advanced_upload", full_path=path, save_path=os.path.basename(path))
# If it's a floder
if os.path.isdir(path):
    input(f"Do you mean: Upload Folder [{path}]")
for dirpath, dirnames, filenames in os.walk(path):
    for filename in filenames:
        full_path = os.path.join(dirpath, filename)
        save_path = os.path.relpath(full_path, os.path.dirname(path))
        print({"full_path": full_path, "save_path": save_path})
        file_split(f"{base_url}/advanced_upload", full_path=full_path, save_path=save_path)
