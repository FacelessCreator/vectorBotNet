import threading
import time
import signal
import sys

import jsonWebsocket
import botNet
import pipeGUIServer

HOST = "0.0.0.0"
PORT = 8080

stop_event = threading.Event()

pipes = dict() # {"output_name": ["input_name"]}

log_from = None
local_log = []

cat_file = None
cat_robot = None

robotServer = None
GUIServer = None

start_time = time.time()

def newGUIEvent(jws: jsonWebsocket.JsonWebsocket):
    global robotServer
    for name in robotServer.getNames():
        message = {"type": "new_client", "name":name, "vector_format":robotServer.getVectorFormat(name), "coefficients_format":robotServer.getCoefficientsFormat(name)}
        GUI_format = robotServer.getGUIFormat(name)
        if GUI_format:
            message["GUI_format"] = GUI_format
        jws.send(message)

def sendVector(robot_from, robot_to, t, vector_from):
    global robotServer
    vector_format_from = robotServer.getVectorFormat(robot_from)
    vector_format_to = robotServer.getVectorFormat(robot_to)
    vector_to = list()
    for i in range(0, len(vector_format_to)):
        if vector_format_to[i] in vector_format_from:
            j = vector_format_from.index(vector_format_to[i])
            vector_to.append(vector_from[j])
        else:
            vector_to.append(None)
    robotServer.sendVector(robot_to, t, vector_to)

def pipeLoop(stop_event: threading.Event):
    global GUIServer, robotServer, pipes, log_from, local_log, cat_file, cat_robot
    while not stop_event.is_set():
        robots_from = robotServer.getNames()
        for robot_from in robots_from:
            t, vect = robotServer.getLastVector(robot_from)
            if vect:
                GUIServer.newVectorEvent(robot_from, t, vect)
                if robot_from in pipes:
                    for robot_to in pipes[robot_from]:
                        sendVector(robot_from, robot_to, t, vect)
                if log_from == robot_from:
                    local_log.append((t, vect))
                    print("{}: {}".format(t, vect))
                if robot_from == cat_robot:
                    cat_file.write("{}: {}\n".format(t, vect))
        time.sleep(0.01)

def consoleLoop(stop_event: threading.Event):
    global robotServer, pipes, log_from, local_log, cat_file, cat_robot, start_time
    while not stop_event.is_set():
        # get input
        print("> ", end="")
        line = ""
        try:
            line = input()
        except EOFError:
            stop_event.set()
            return
        args = line.split()
        if (len(args) == 0):
            continue
        if args[0] == "exit":
            stop_event.set()
            return
        elif args[0] == "help" or args[0] == "?":
            print("Nobody helps you")
        elif args[0] == "lr":
            longForm = False
            if len(args) > 1 and args[1] == "-l":
                longForm = True
            for name in robotServer.getNames():
                if longForm:
                    vector_format = robotServer.getVectorFormat(name)
                    coefficients_format = robotServer.getCoefficientsFormat(name)
                    print("{}: {} {}".format(name, vector_format, coefficients_format))
                else:
                    print(name, end=" ")
            if not longForm:
                print()
        elif args[0] == "log":
            if len(args) < 3:
                print("not enough args")
                continue
            name = args[1]
            value = int(args[2])
            if not name in robotServer.getNames():
                print('no such robot "{}"'.format(name))
                continue
            if not (value == 1 or value == 0):
                print('wrong value "{}"'.format(value))
                continue
            robotServer.setLogging(name, value)
        elif args[0] == "control":
            if len(args) < 3:
                print("not enough args")
                continue
            name = args[1]
            value = int(args[2])
            if not name in robotServer.getNames():
                print('no such robot "{}"'.format(name))
                continue
            if not (value == 1 or value == 0):
                print('wrong value "{}"'.format(value))
                continue
            robotServer.setControlling(name, value)
        elif args[0] == "clear":
            if len(args) < 2:
                print("not enough args")
                continue
            name = args[1]
            if not name in robotServer.getNames():
                print('no such robot "{}"'.format(name))
                continue
            robotServer.clear(name)
        elif args[0] == "wtf":
            if len(args) < 2:
                print("not enough args")
                continue
            name = args[1]
            if not name in robotServer.getNames():
                print('no such robot "{}"'.format(name))
                continue
            vector_format = robotServer.getVectorFormat(name)
            coefficients_format = robotServer.getCoefficientsFormat(name)
            print("{}: {} {}".format(name, vector_format, coefficients_format))
        elif args[0] == "k":
            if len(args) < 2:
                print("not enough args")
                continue
            name = args[1]
            if not name in robotServer.getNames():
                print('no such robot "{}"'.format(name))
                continue
            coefficients = []
            try:
                for i in range(2, len(args)):
                    coefficients.append(float(args[i]))
                robotServer.setCoefficients(name, coefficients)
            except ValueError:
                print("the coefficients must be float")
                continue
        elif args[0] == "lp":
            for pipe_from in pipes:
                print('from "{}" to '.format(pipe_from),end="")
                for pipe_to in pipes[pipe_from]:
                    print('"{}" '.format(pipe_to), end="")
                print()
        elif args[0] == "pipe":
            if len(args) < 2:
                print("not enough args")
                continue
            if args[1] == "-r":
                if len(args) < 4:
                    print("not enough args")
                    continue
                pipe_from = args[2]
                pipe_to = args[3]
                if not pipe_from in pipes or not pipe_to in pipes[pipe_from]:
                    print("pipe not found")
                    continue
                pipes[pipe_from].remove(pipe_to)
                if len(pipes[pipe_from]) == 0:
                    pipes.pop(pipe_from)
            else:
                if len(args) < 3:
                    print("not enough args")
                    continue
                pipe_from = args[1]
                pipe_to = args[2]
                names = robotServer.getNames()
                if not pipe_from in names or not pipe_to in names:
                    print("robots not found")
                    continue
                if not pipe_from in pipes:
                    pipes[pipe_from] = []
                pipes[pipe_from].append(pipe_to)
        elif args[0] == "trace":
            if len(args) < 2:
                print("not enough args")
                continue
            name = args[1]
            if not name in robotServer.getNames():
                print('no such robot "{}"'.format(name))
                continue
            log_from = name
            local_log.clear()
            trace_start_time = time.time()
            # wait for signal from user
            try:
                line = input()
            except EOFError:
                stop_event.set()
                return
            log_from = None
            print("Total: accepted {} packages in {} seconds".format(len(local_log), int(time.time() - trace_start_time)))
        elif args[0] == "send":
            if len(args) < 2:
                print("not enough args")
                continue
            name = args[1]
            if not name in robotServer.getNames():
                print('no such robot "{}"'.format(name))
                continue
            vect = []
            try:
                for i in range(2, len(args)):
                    vect.append(float(args[i]))
                robotServer.sendVector(name, time.time() - start_time, vect)
            except ValueError:
                print("the coefficients must be float")
                continue
        elif args[0] == "cat":
            if len(args) == 1:
                if cat_robot:
                    print("{} > {}".format(cat_robot, cat_file.name))
                continue
            if args[1] == "-a":
                if len(args) < 4:
                    print("not enough args")
                    continue
                robot_in = args[2]
                if not robot_in in robotServer.getNames():
                    print('no such robot "{}"'.format(robot_in))
                    continue
                file_name = args[3]
                try:
                    cat_file = open(file_name, "a")
                    cat_robot = robot_in
                except Exception as e:
                    print(e)
            elif args[1] == "-r":
                cat_robot = None
                cat_file.close()
            else:
                if len(args) < 3:
                    print("not enough args")
                    continue
                robot_in = args[1]
                if not robot_in in robotServer.getNames():
                    print('no such robot "{}"'.format(robot_in))
                    continue
                file_name = args[2]
                try:
                    cat_file = open(file_name, "w")
                    cat_robot = robot_in
                except Exception as e:
                    print(e)
        else:
            print('unknown command "{}". Use "help" to view list of commands'.format(args[0]))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("wrong args; use ROBOTS_PORT GUI_PORT")
        exit()
    HOST = "0.0.0.0"
    ROBOTS_PORT = sys.argv[1]
    GUI_PORT = sys.argv[2]

    robotServer = botNet.BotNetServer(HOST, ROBOTS_PORT)
    GUIServer = pipeGUIServer.PipeGUIServer(HOST, GUI_PORT)

    robotServer.newClientEvent = GUIServer.newClientEvent
    robotServer.lostClientEvent = GUIServer.lostClientEvent
    GUIServer.newGUIEvent = newGUIEvent

    console_thread = threading.Thread(target=consoleLoop, args=(stop_event,))
    pipe_thread = threading.Thread(target=pipeLoop, args=(stop_event,), daemon=True)
    
    console_thread.start()
    pipe_thread.start()
    
    console_thread.join()