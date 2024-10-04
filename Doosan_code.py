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
    while (force < 1.5 and check_motion() != 0):        # keep moving until the force equals 1.5 newton (150 grams) or it reaches the end position
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
    wait(3)

    triggerstatus = client_socket_read(socket, -1, -1)[1].decode()[:-2]

    if triggerstatus != "1":
        tp_log("Trigger failed: " + str(triggerstatus))
        return 0

    wait(1)  # Just to be sure, this can probably be removed

    client_socket_write(socket, (cel_data + "\r\n").encode())   #GVC013
    getvaluestatus, rec, _empty = str(client_socket_read(socket, -1, -1)[1].decode()).split("\r\n")

    if getvaluestatus == "1":
        #tp_log("GetValue successful: " + str(getvaluestatus))
        rec = str(rec).split(",")
    else:
        tp_log("GetValue failed: " + str(getvaluestatus))

    #tp_log("Received list:" + str(rec))

    client_socket_close(socket)
    
    return rec

def add_vector_to_pos_xy(_pos, angle, distance):
    _pos[1] = _pos[1] + sin(d2r(_pos[2] + angle)) * distance
    _pos[0] = _pos[0] + cos(d2r(_pos[2] + angle)) * distance
    return _pos

def soldeer():      #not functional
    X_Y_R = get_data_from_cognex('GVC013')
    if (X_Y_R == ['']):
        tp_popup('No mold detected please place mold in the detectable square', pm_type=DR_PM_MESSAGE, button_type=1)
        return 0
    _pos_x = float(X_Y_R[0])
    _pos_y = float(X_Y_R[1])
    _pos_r = float(X_Y_R[2]) - 0.8
    _pos = [_pos_x, _pos_y, _pos_r]
    #tp_log("angle: " + str(_pos_r))

    _pos = add_vector_to_pos_xy(_pos, 270, 15)
    _pos = add_vector_to_pos_xy(_pos, 180, 10)

    # measure point 1 height
    _pos_1_measure = list(_pos)
    _pos_1_measure = add_vector_to_pos_xy(_pos_1_measure, 180, 5)
    rotate_head_angle(_pos_1_measure[2] + 180)
    movel(add_pose(posx(_pos_1_measure[0], _pos_1_measure[1], 100, 0,0,0), angleToAA(_pos_1_measure[2] + 180)), vel=velocity, acc=accelleration)
    move_until_feedback(add_pose(posx(_pos_1_measure[0], _pos_1_measure[1], 50, 0,0,0), angleToAA(_pos_1_measure[2] + 180)))
    _pos_1, _i = get_current_posx()
    _pos_1[3] = 0
    _pos_1[4] = 0
    _pos_1[5] = 0
    movel(add_pose(posx(_pos_1_measure[0], _pos_1_measure[1], 100, 0, 0, 0), angleToAA(_pos_1_measure[2] + 180)), vel=velocity, acc=accelleration)

    # measure point 2 height
    _pos_2_measure = add_vector_to_pos_xy(_pos_1_measure, 0, 170)
    rotate_head_angle(_pos_1_measure[2])
    movel(add_pose(posx(_pos_2_measure[0], _pos_2_measure[1], 100, 0, 0, 0), angleToAA(_pos_2_measure[2])), vel=velocity, acc=accelleration)
    move_until_feedback(add_pose(posx(_pos_2_measure[0], _pos_2_measure[1], 50, 0, 0, 0), angleToAA(_pos_2_measure[2])))
    _pos_2, _i = get_current_posx()
    _pos_2[3] = 0
    _pos_2[4] = 0
    _pos_2[5] = 0
    movel(add_pose(posx(_pos_2_measure[0], _pos_2_measure[1], 100, 0, 0, 0), angleToAA(_pos_2_measure[2])), vel=velocity, acc=accelleration)

    _z_offset = (_pos_1[2] - _pos_2[2])/8

    get_to_point_by_angle(_pos[0], _pos[1], 85 + _z_offset*0, _pos[2] + 180, 10, 2, True)

    for i in range(8):
        _pos = add_vector_to_pos_xy(_pos, 0, 20)
        get_to_point_by_angle(_pos[0], _pos[1], 85 + _z_offset*i, _pos[2] + 180, 10, 2, True)

    _pos = add_vector_to_pos_xy(_pos, 0, 4)
    get_to_point_by_angle(_pos[0], _pos[1], 85 + _z_offset*8, _pos[2], 10, 2, True)

    for i in range(8):
        _pos = add_vector_to_pos_xy(_pos, 180, 20)
        get_to_point_by_angle(_pos[0], _pos[1], 85 + _z_offset*(8-i), _pos[2], 10, 2, True)
    return 0

def calculate_offset_center(_posx)
    _posx[2] = 100
    movel(_posx, acc=accelleration, vel=velocity)
    _posx[2] = 80
    move_until_feedback(_posx)
    z1 = 1.825575256347656 + 80.89949 # pre determant value in mm       # 1.825575256347656 is the value of hitting the table
    _pos, _i = get_current_posx() # pose in which the robot stops and take z value 
    z2 = _pos[2]
    offset = (z1-z2)/tan(45/180*3.14) # calculate offset trough formula
    return offset, z2
  
def test():
    get_to_point_by_angle(394.7, 415.5, 70,   0, 20, 2, True)
    get_to_point_by_angle(394.7, 415.5, 70,  90, 20, 2, True)
    get_to_point_by_angle(394.7, 415.5, 70, 180, 20, 2, True)
    get_to_point_by_angle(394.7, 415.5, 70, 270, 20, 2, True)
    return 0

def function_test():
    #get_data_from_cognex('GVC013')
    soldeer()
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
boot_up_pos, _i = get_current_posx()
boot_up_pos[2] += 40
movel(boot_up_pos, vel=velocity, acc=accelleration)

move_home(DR_HOME_TARGET_USER)

while True:
    tp_popup('Start new soldering job?', pm_type=DR_PM_MESSAGE, button_type=0)
    #test()
    function_test()
    #exit()
    move_home(DR_HOME_TARGET_USER)
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
