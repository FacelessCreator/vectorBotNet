import threading
import time
import signal
import sys

import botNet

HOST = "0.0.0.0"
PORT = 8080

stop_event = threading.Event()

pipes = dict() # {"output_name": ["input_name"]}

log_from = None
local_log = []

cat_file = None
cat_robot = None

start_time = time.time()

def pipeLoop(server: botNet.BotNetServer, stop_event: threading.Event):
    global pipes, log_from, local_log, cat_file, cat_robot
    while not stop_event.is_set():
        names = server.getNames()
        for name in names:
            t, vect = server.getLastVector(name)
            if vect:
                if name in pipes:
                    for pipe_to in pipes[name]:
                        server.sendVector(pipe_to, t, vect)
                if log_from == name:
                    local_log.append((t, vect))
                    print("{}: {}".format(t, vect))
                if name == cat_robot:
                    cat_file.write("{}: {}\n".format(t, vect))
        time.sleep(0.01)

def consoleLoop(server: botNet.BotNetServer, stop_event: threading.Event):
    global pipes, log_from, local_log, cat_file, cat_robot, start_time
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
            for name in server.getNames():
                if longForm:
                    vector_format = server.getVectorFormat(name)
                    coefficients_format = server.getCoefficientsFormat(name)
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
            if not name in server.getNames():
                print('no such robot "{}"'.format(name))
                continue
            if not (value == 1 or value == 0):
                print('wrong value "{}"'.format(value))
                continue
            server.setLogging(name, value)
        elif args[0] == "control":
            if len(args) < 3:
                print("not enough args")
                continue
            name = args[1]
            value = int(args[2])
            if not name in server.getNames():
                print('no such robot "{}"'.format(name))
                continue
            if not (value == 1 or value == 0):
                print('wrong value "{}"'.format(value))
                continue
            server.setControlling(name, value)
        elif args[0] == "clear":
            if len(args) < 2:
                print("not enough args")
                continue
            name = args[1]
            if not name in server.getNames():
                print('no such robot "{}"'.format(name))
                continue
            server.clear(name)
        elif args[0] == "wtf":
            if len(args) < 2:
                print("not enough args")
                continue
            name = args[1]
            if not name in server.getNames():
                print('no such robot "{}"'.format(name))
                continue
            vector_format = server.getVectorFormat(name)
            coefficients_format = server.getCoefficientsFormat(name)
            print("{}: {} {}".format(name, vector_format, coefficients_format))
        elif args[0] == "k":
            if len(args) < 2:
                print("not enough args")
                continue
            name = args[1]
            if not name in server.getNames():
                print('no such robot "{}"'.format(name))
                continue
            coefficients = []
            try:
                for i in range(2, len(args)):
                    coefficients.append(float(args[i]))
                server.setCoefficients(name, coefficients)
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
                names = server.getNames()
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
            if not name in server.getNames():
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
            if not name in server.getNames():
                print('no such robot "{}"'.format(name))
                continue
            vect = []
            try:
                for i in range(2, len(args)):
                    vect.append(float(args[i]))
                server.sendVector(name, time.time() - start_time, vect)
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
                if not robot_in in server.getNames():
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
                if not robot_in in server.getNames():
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
        print("wrong args; use HOST PORT")
        exit()
    HOST = sys.argv[1]
    PORT = sys.argv[2]    

    server = botNet.BotNetServer(HOST, PORT)

    console_thread = threading.Thread(target=consoleLoop, args=(server, stop_event))
    pipe_thread = threading.Thread(target=pipeLoop, args=(server, stop_event), daemon=True)
    
    console_thread.start()
    pipe_thread.start()
    
    console_thread.join()