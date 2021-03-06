import os,socket,threading,time
import subprocess,sys,select

allow_delete = True
local_ip = "127.0.0.1"
local_port = 8000
currdir=os.path.abspath('.')

class Server:
    def __init__(self):
        self.host = local_ip
        self.port = local_port
        self.size = 1024
        self.server = None
        self.threads = []

    def open_socket(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host,self.port))
        self.server.listen(5)
    
    def run(self):
        self.open_socket()
        input = [self.server]
        running = 1
        print 'On', local_ip, ':', local_port
        
        while running:
            inputready,outputready,exceptready = select.select(input,[],[])
            for s in inputready:
                if s == self.server:
                    c = FTPserverThread(self.server.accept())
                    c.start()
                    self.threads.append(c)
                elif s == sys.stdin:
                    junk = sys.stdin.readline()
                    running = 0
        self.server.close()
        for c in self.threads:
            c.join()

class FTPserverThread(threading.Thread):
    def __init__(self,(conn,addr)):
        self.conn=conn
        self.addr=addr
        self.basewd=currdir
        self.cwd=self.basewd
        self.rest=True
        self.pasv_mode=True
        threading.Thread.__init__(self)
        self.flagu = 0
        self.flagp = 0

    def run(self):
        self.conn.send('220 Selamat Datang!\r\nSilahkan Masukan USERNAME dan PASSWORD jika ingin menggunakan semua command kecuali HELP dan QUIT.\r\nCommand HELP jika ingin mengetahui list command yang tersedia')
        while True:
            cmd=self.conn.recv(1024)
            if not cmd: 
                break
            else:
                print 'Recieved:',cmd
                try:
                    func=getattr(self,cmd[:4].strip().upper())
                    func(cmd)
                except Exception,e:
                    print 'ERROR:',e
                    self.conn.send('202 Command tidak tersedia di FTProgjar')

    def USER(self,cmd):
        user=cmd.strip().split()[1]
        if user == "joke":
            self.flagu = 1
            self.conn.send('331 USERNAME BENAR MASUKKAN PASSWORD dengan command PASS "password_anda".\r\n')
        else:
            self.conn.send('530 sorry.\r\n Masukan Username yang benar.\r\n')

    def PASS(self,cmd):
        password=cmd.strip().split()[1]
        if password == "fun":
            self.flagp = 1
            self.conn.send('230 PASSWORD BENAR.\r\Selamat Datang Joke!')
        else:
            self.conn.send('530 sorry.\r\n Masukan Password yang benar.\r\n')

    
    def QUIT(self,cmd):
        self.conn.send('221 Selamat tinggal JOKE!.\r\n')

    def PWD(self,cmd):
        if self.flagu==1 and self.flagp==1:
            cwd=os.path.relpath(self.cwd,self.basewd)
            if cwd=='.':
                cwd='/'
            else:
                cwd='/'+cwd
            self.conn.send('257 \"%s\"\r\n' % cwd)
        else:
            self.conn.send('Masukan Username dan Password dahulu')
   
    def CWD(self,cmd):
        if self.flagu==1 and self.flagp==1:
            chwd=cmd[4:-2]
            if chwd=='/':
                self.cwd=self.basewd
                self.conn.send('250 OK.\r\n')
            elif chwd[0]=='/':
                self.cwd=os.path.join(self.basewd,chwd[1:])
                self.conn.send('250 OK.\r\n')
            elif os.path.isdir(os.path.join(self.cwd,chwd)):
                self.cwd=os.path.join(self.cwd,chwd)
                self.conn.send('250 OK.\r\n')
            else:
                self.conn.send('530 GAGAL.\r\n')
        else:
            self.conn.send('Masukan Username dan Password dahulu')
                
    def LIST(self,cmd):
        if self.flagu==1 and self.flagp==1:
            data = "\n"
            for filename in os.listdir(self.cwd):
                data = data + filename + "\n"
            self.conn.send(data)
        else:
            self.conn.send('Masukan Username dan Password dahulu')
	
    def MKD(self,cmd):
        if self.flagu==1 and self.flagp==1:
            dn=os.path.join(self.cwd,cmd[4:-2])
            os.mkdir(dn)
            self.conn.send('257 Directory created.\r\n')
        else:
            self.conn.send('Masukan Username dan Password dahulu')

    def RMD(self,cmd):
        if self.flagu==1 and self.flagp==1:
            dn=os.path.join(self.cwd,cmd[4:-2])
            if allow_delete:
                os.rmdir(dn)
                self.conn.send('250 Directory deleted.\r\n')
            else:
                self.conn.send('450 Not allowed.\r\n')
        else:
            self.conn.send('Masukan Username dan Password dahulu')


    def DELE(self,cmd):
        if self.flagu==1 and self.flagp==1:
            fn=os.path.join(self.cwd,cmd[5:-2])
            if allow_delete:
                os.remove(fn)
                self.conn.send('250 File deleted.\r\n')
            else:
                self.conn.send('450 Not allowed.\r\n')
        else:
            self.conn.send('Masukan Username dan Password dahulu')

    def RNFR(self,cmd):
        if self.flagu==1 and self.flagp==1:
            self.rnfn=os.path.join(self.cwd,cmd[5:-2])
            self.conn.send('350 Ready.\r\n')
        else:
            self.conn.send('Masukan Username dan Password dahulu')

    def RNTO(self,cmd):
        if self.flagu==1 and self.flagp==1:
            fn=os.path.join(self.cwd,cmd[5:-2])
            os.rename(self.rnfn,fn)
            self.conn.send('250 File renamed.\r\n')
        else:
            self.conn.send('Masukan Username dan Password dahulu')

    def RETR(self,cmd):
        cmd1=cmd.split("\r\n")
        name=cmd1[0].split("RETR ")[1]
        file_path = os.path.join(os.getcwd(),name.strip())
        print 'Downloading:',file_path
        size = str(os.path.getsize(file_path))        
        self.conn.send(size)
        fileopen = open(name,"rb")
        data = fileopen.read(1024)
        while (1):
            if not data:
                break
            self.conn.send(data)
            data = fileopen.read(1024)
        fileopen.close()
        print 'done\r\n'
        self.conn.send('226 Transfer complete.\r\n')

    def STOR(self,cmd):
        if self.flagu==1 and self.flagp==1:
            cmd1=cmd.split("\r\n")
            name=cmd1[0].split("STOR ")
            fn=os.path.join(self.cwd,name[1])
            print 'Uplaoding:',fn
            fileopen=open(fn,'wb')
            size=int(cmd.split("\r\n")[1])
            data = ""
            while True:
                if len(data)==size:
                    break
                else:
                    data+=self.conn.recv(1024)
            fileopen.write(data)
            fileopen.close()
            self.conn.send('226 Transfer complete.\r\n')
        else:
            self.conn.send('Masukan Username dan Password dahulu')

    def HELP(self,cmd):
        result = ""
        kata=cmd.split(" ")
        if kata[0] == "HELP" and len(kata)==1:
            result += "Komen yang di sediakan:\n"
            result += "USER PASS CWD QUIT RETR STOR RNFR\n"
            result += "RNTO DELE RMD MKD PWD LIST HELP\n"
            result += "Selamat ^-^\r\n"
        elif kata[1]!="":
            tmp=kata[1].split("\r\n")
            if tmp[0]=="USER" or tmp[0]=="PASS" or tmp[0]=="QUIT" or tmp[0]=="PWD" or tmp[0]=="LIST" or tmp[0]=="CWD" or tmp[0]=="RETR" or tmp[0]=="STOR" or tmp[0]=="RNFR" or tmp[0]=="RNTO" or tmp[0]=="DELE" or tmp[0]=="RMD" or tmp[0]=="MKD" or tmp[0]=="HELP":
                result += tmp[0] + " Terserdia pada FTProgjar Server.\r\n"
            else:
                result += tmp[0] + " Tidak tersedia pada FTProgjar Server.\r\n"
        self.conn.send(result)

if __name__=='__main__':
    s = Server()
    s.run()
