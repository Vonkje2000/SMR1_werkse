from DRCF import *

degrees_offset_to_zero = 90
def angleToAA(Angle):
    Angle *= -1
    return posx(0,0,0,0,180,Angle + degrees_offset_to_zero)

def get_to_point_by_angle(_pos_x, _pos_y, _pos_z, _Angle, _distance, _s_wait_time, force_feedback):
    y_offset = sin(_Angle/180*3.14)*_distance
    x_offset = cos(_Angle/180*3.14)*_distance

    #set rotation of the head
    rotate_head_angle(_Angle)

    #position to the side
    movel(add_pose(posx(_pos_x + x_offset, _pos_y + y_offset, _pos_z + _distance, 0, 0, 0), angleToAA(_Angle)), vel=velocity, acc=accelleration)

    #final position
    if(force_feedback):
        move_until_feedback(add_pose(posx(_pos_x           , _pos_y           , _pos_z            , 0, 0, 0), angleToAA(_Angle)))
    else:
        movel(add_pose(posx(_pos_x           , _pos_y           , _pos_z            , 0, 0, 0), angleToAA(_Angle)), vel=30, acc=30)

    wait(_s_wait_time)

    #back to position on the side
    movel(add_pose(posx(_pos_x + x_offset, _pos_y + y_offset, _pos_z + _distance, 0, 0, 0), angleToAA(_Angle)), vel=velocity, acc=accelleration)
    return 0

head_angle = 180
def rotate_head_angle(Angle):
    global head_angle
    max_degrees = 360
    #min_degrees = -100
    min_degrees = 0
    arm_position, _i = get_current_posx()
    arm_position[3] = 0
    arm_position[4] = 0
    arm_position[5] = 0

    while (Angle > max_degrees):
        Angle = Angle - 360
    while (Angle < min_degrees):
        Angle = Angle + 360

    while (head_angle < Angle):
        head_angle += 90
        if (head_angle > Angle):
            head_angle = Angle
        movel(add_pose(arm_position, angleToAA(head_angle)), vel=30, acc=30)

    while (head_angle > Angle):
        head_angle -= 90
        if (head_angle < Angle):
            head_angle = Angle
        movel(add_pose(arm_position, angleToAA(head_angle)), vel=30, acc=30)
    return 0

def move_until_feedback(_posx):
    amovel(_posx, vel=5, acc=1)
    default_force = get_external_torque()[1]
    force = get_external_torque()[1] - default_force
    #while (forces[2] < 1.5 and get_current_posx()[0][2] <= _posx[2]+0.2):    #1.5 = force    kg/10
    while (force < 1.5):
        force = get_external_torque()[1] - default_force
    stop(DR_SSTOP)
    #tp_log(str(force))
    return 0

def get_data_from_cognex(cel_data):
    ### Configuration of camera settings, adjust where needed ###
    port = 10000
    ip = "192.168.137.10"

    ### Connect to camera and return status ###
    socket = client_socket_open(ip, port)

    ### After connecting the camera first sends a welcome message and asks for username and password ###
    receive = client_socket_read(socket, -1, -1)[1].decode()
    #tp_log(str(receive))
    client_socket_write(socket, "admin\r\n".encode())   #username + carage return, new line character

    ### Asked for a password ###
    receive = client_socket_read(socket, -1, -1)[1].decode()
    #tp_log(str(receive))
    client_socket_write(socket, "\r\n".encode())        #password(empty) + carage return, new line character

    ### user logged IN message ###
    receive = client_socket_read(socket, -1, -1)[1].decode()
    #tp_log(str(receive))

    ### Trigger camera, only works if camera is in ONLINE mode
    #client_socket_write(socket, "SW8\r\n".encode())     #SW set event and wait gives an error and dont know why
    client_socket_write(socket, "SE8\r\n".encode())      #SE set event does work but does not wait
    wait(0.5)

    triggerstatus = client_socket_read(socket, -1, -1)[1].decode()[:-2]

    if triggerstatus == "1":
        tp_log("Trigger successful: " + str(triggerstatus))
    else:
        tp_log("Trigger failed: " + str(triggerstatus))

    wait(1)  # Just to be sure, this can probably be removed

    client_socket_write(socket, (cel_data + "\r\n").encode())   #GVC013
    getvaluestatus, rec, _empty = str(client_socket_read(socket, -1, -1)[1].decode()).split("\r\n")

    if getvaluestatus == "1":
        tp_log("GetValue successful: " + str(getvaluestatus))
    else:
        tp_log("GetValue failed: " + str(getvaluestatus))

    tp_log("Received list:" + str(str(rec).split(",")))

    client_socket_close(socket)
    return 0

def calculate_offset_center(_posx)
    _posx[2] = 100
    movel(_posx, acc=accelleration, vel=velocity)
    _posx[2] = 80
    move_until_feedback(_posx)
    z1 = 1.825575256347656 + 80.89949 #pre determant value in mm       # 1.825575256347656 is the value of hitting the table
    _pos, _i = get_current_posx() # pose in which the robot stops and take z value 
    z2 = _pos[2]
    offset = (z1-z2)/tan(45/180*3.14) #calculate offset trough formula
return offset, z2

def test():
    get_to_point_by_angle(394.7, 415.5, 70,   0, 20, 2, True)
    get_to_point_by_angle(394.7, 415.5, 70,  90, 20, 2, True)
    get_to_point_by_angle(394.7, 415.5, 70, 180, 20, 2, True)
    get_to_point_by_angle(394.7, 415.5, 70, 270, 20, 2, True)
    return 0

def function_test():
    get_data_from_cognex('GVC013')
    return 0

# start of define variables of the code
BL = posx(394.7, 415.5, 0,0,0,0)
BR = posx(396.4, 717.2, 0,0,0,0)
TL = posx( 96.6, 416.4, 0,0,0,0)
TR = posx(100.4, 729.7, 0,0,0,0)

#Zbottom = posx(0, 0, 65.9, 0, 0, 0)
Zbottom = posx(0, 0, 85, 0, 0, 0)
Z_10_CM_up = posx(0, 0, 100, 0, 0, 0)

accelleration = 100
velocity = 100
# end of defined variables

# start of the code
tp_popup('Lookout robot arm starts homing.', pm_type=DR_PM_MESSAGE, button_type=1)
move_home(DR_HOME_TARGET_USER)

while True:
    tp_popup('Start new soldering job?', pm_type=DR_PM_MESSAGE, button_type=0)
    #test()
    function_test()
    #exit()
# end of the code

#force_ext = get_tool_force(DR_WORLD)   # force_ext: external force of the tool based on the world coordinate
#set_desired_force                      # force detection
#set_tool_digital_output                # control output on tool head
#set_mode_analog_output                 # for variable output control
#tp_popup                               # pop up on touch pendent
#tp_log                                 # log to the log file
#d2r(x)                                 # convert degrees to radials
#client_socket_open                     # open tcp socket
#External Vision Commands
