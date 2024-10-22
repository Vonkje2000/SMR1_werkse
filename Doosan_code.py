from DRCF import *

### function to change the direction of the head without changing the other rotations because it is only needed to rotate 1 axis ###
degrees_offset_to_zero = 90
def angleToAA(Angle):
    Angle *= -1
    return posx(0,0,0,0,180,Angle + degrees_offset_to_zero)

### function to get to a point in a 45 degree angle this also triggers the extrude command to solder ###
def get_to_point_by_angle(_pos_x, _pos_y, _pos_z, _Angle, _distance, _s_wait_time, force_feedback):
    y_offset = sin(_Angle/180*3.14)*_distance
    x_offset = cos(_Angle/180*3.14)*_distance

    #set rotation of the head
    rotate_head_angle(_Angle)

    #position to the side
    movel(add_pose(posx(_pos_x + x_offset, _pos_y + y_offset, _pos_z + _distance, 0, 0, 0), angleToAA(_Angle)), vel=velocity, acc=accelleration)

    async_send_extrude_command(100)   #80
    #final position
    if(force_feedback):
        move_until_feedback(add_pose(posx(_pos_x           , _pos_y           , _pos_z            , 0, 0, 0), angleToAA(_Angle)))
    else:
        movel(add_pose(posx(_pos_x           , _pos_y           , _pos_z            , 0, 0, 0), angleToAA(_Angle)), vel=30, acc=30)
    
    wait(_s_wait_time / 5 * 1)
    send_extrude_command(100)   #80
    wait(_s_wait_time / 5 * 1)
    send_extrude_command(100)   #80
    wait(_s_wait_time / 5 * 1)
    wait(_s_wait_time / 5 * 1)
    wait(_s_wait_time / 5 * 1)

    #back to position on the side
    movel(add_pose(posx(_pos_x + x_offset, _pos_y + y_offset, _pos_z + _distance, 0, 0, 0), angleToAA(_Angle)), vel=velocity, acc=accelleration)
    return 0

### because the robot can try to rotate outside the limit of 360 to -360 degrees and then generate an error ###
### this function remembers the angle of the head and then makes waypoint in a direction the head can rotate ###
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

### this function moves the robot to a specified location and stops when it is there or when it has force feedback ###
def move_until_feedback(_posx):
    amovel(_posx, vel=5, acc=1)
    default_force = get_external_torque()[1]
    force = get_external_torque()[1] - default_force
    #while (forces[2] < 1.5 and get_current_posx()[0][2] <= _posx[2]+0.2):    #1.5 = force    kg/10
    while (force < 2.0 and check_motion() != 0):        # keep moving until the force equals 1.5 newton (150 grams) or it reaches the end position
        force = get_external_torque()[1] - default_force
    stop(DR_SSTOP)
    #tp_log(str(force))
    return 0

### Function for the communication with the cognex camera ###
def get_data_from_cognex(cel_data):
    ### turn light on ###
    set_mode_analog_output(ch=1, mod=DR_ANALOG_CURRENT)  # out ch1 = current mode
    set_analog_output(ch=1, val=20.0)
    
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

    ### turn light off ###
    set_mode_analog_output(ch=1, mod=DR_ANALOG_VOLTAGE)  # out ch1 = voltage mode
    set_analog_output(ch=1, val=0.1)
    
    return rec

### function to send an amount of steps that the stepper on the ESP32 can rotate ###
def send_extrude_command(steps=10):
    port = 4242
    ip = "192.168.137.52"

    socket = client_socket_open(ip, port)

    client_socket_write(socket, (str(steps) + "\r\n").encode())

    status = client_socket_read(socket, -1, -1)[1].decode()
    
    client_socket_close(socket)

    return 0

### function to send an amount of steps that the stepper on the ESP32 can rotate without waithing until it is done ###
def async_send_extrude_command(steps):
    port = 4242
    ip = "192.168.137.40"

    socket = client_socket_open(ip, port)

    client_socket_write(socket, (str(steps) + "\r\n").encode())

    client_socket_close(socket)

    return 0

### function to add a vector to a XY position ###
def add_vector_to_pos_xy(_pos, angle, distance):
    _pos[1] = _pos[1] + sin(d2r(_pos[2] + angle)) * distance
    _pos[0] = _pos[0] + cos(d2r(_pos[2] + angle)) * distance
    return _pos

### function that uses all the other functions to do a compleet solder job ###
def soldeer():
    X_Y_R = get_data_from_cognex('GVC019')
    if (X_Y_R == ['']):
        tp_popup('No mold detected please place mold in the detectable square', pm_type=DR_PM_MESSAGE, button_type=1)
        return 0

    _pos_x = float(X_Y_R[0])
    _pos_y = float(X_Y_R[1])
    _pos_r = float(X_Y_R[2])
    _mold_number = int(X_Y_R[3])

    if _mold_number == 0:
        _pos_x += 0
        _pos_y += 0
        _pos_r += -1.5           # - degrees is rotating clockwise, + degrees is rotating anti clockwise

    if _mold_number == 1:
        _pos_x += 0
        _pos_y += 0
        _pos_r += 0

    if _mold_number == 2:
        _pos_x += 0
        _pos_y += 0
        _pos_r += 0

    _pos = [_pos_x, _pos_y, _pos_r]
    #tp_log("number: " + str(_mold_number))
    #tp_log("offset: " + str(offset))

    if _mold_number == 0 or _mold_number == 1:
        _pos = add_vector_to_pos_xy(_pos, 270, 9)  # distance from data matrix to the aluminium
        _pos = add_vector_to_pos_xy(_pos, 180, 13)  # distance from data matrix 90 degrees of to the aluminium
    elif _mold_number == 2:
        _pos = add_vector_to_pos_xy(_pos, 270, -49)  # distance from data matrix to the aluminium needs to be negative. the metrix is at the other side
        _pos = add_vector_to_pos_xy(_pos, 180, 15)  # distance from data matrix 90 degrees of to the aluminium
    else:
        return 0

    _offset_pos = add_vector_to_pos_xy([0,0,_pos_r], 0, offset)
    _offset_pos_inverse = add_vector_to_pos_xy([0, 0, _pos_r], 180, offset)

    # measure point 1 height
    _pos_1_measure = list(_pos)
    _pos_1_measure = add_vector_to_pos_xy(_pos_1_measure, 180, 5)
    rotate_head_angle(_pos_1_measure[2] + 180)
    movel(add_pose(posx(_pos_1_measure[0] + _offset_pos[0], _pos_1_measure[1] + _offset_pos[1], z_height + 20, 0,0,0), angleToAA(_pos_1_measure[2] + 180)), vel=velocity, acc=accelleration)
    move_until_feedback(add_pose(posx(_pos_1_measure[0] + _offset_pos[0], _pos_1_measure[1] + _offset_pos[1], 50, 0,0,0), angleToAA(_pos_1_measure[2] + 180)))
    _pos_1, _i = get_current_posx()
    _pos_1[3] = 0
    _pos_1[4] = 0
    _pos_1[5] = 0
    movel(add_pose(posx(_pos_1_measure[0] + _offset_pos[0], _pos_1_measure[1] + _offset_pos[1], z_height + 20, 0, 0, 0), angleToAA(_pos_1_measure[2] + 180)), vel=velocity, acc=accelleration)

    # measure point 2 height
    _pos_2_measure = add_vector_to_pos_xy(_pos_1_measure, 0, 169)
    rotate_head_angle(_pos_1_measure[2])
    movel(add_pose(posx(_pos_2_measure[0] + _offset_pos_inverse[0], _pos_2_measure[1] + _offset_pos_inverse[1], z_height + 20, 0, 0, 0), angleToAA(_pos_2_measure[2])), vel=velocity, acc=accelleration)
    move_until_feedback(add_pose(posx(_pos_2_measure[0] + _offset_pos_inverse[0], _pos_2_measure[1] + _offset_pos_inverse[1], 50, 0, 0, 0), angleToAA(_pos_2_measure[2])))
    _pos_2, _i = get_current_posx()
    _pos_2[3] = 0
    _pos_2[4] = 0
    _pos_2[5] = 0
    movel(add_pose(posx(_pos_2_measure[0] + _offset_pos_inverse[0], _pos_2_measure[1] + _offset_pos_inverse[1], z_height + 20, 0, 0, 0), angleToAA(_pos_2_measure[2])), vel=velocity, acc=accelleration)

    _z_offset = (_pos_2[2] - _pos_1[2])/8

    get_to_point_by_angle(_pos[0] + _offset_pos[0], _pos[1] + _offset_pos[1], _pos_1[2] + _z_offset*0, _pos[2] + 180, 10, 20, True)

    for i in range(8):
        _pos = add_vector_to_pos_xy(_pos, 0, 20)
        get_to_point_by_angle(_pos[0] + _offset_pos[0], _pos[1] + _offset_pos[1], _pos_1[2] + _z_offset*i, _pos[2] + 180, 10, 20, True)
        
    _pos = add_vector_to_pos_xy(_pos, 90, 4)  # distance from data matrix to the aluminium
    _pos = add_vector_to_pos_xy(_pos, 0, 4)
    get_to_point_by_angle(_pos[0] + _offset_pos_inverse[0], _pos[1] + _offset_pos_inverse[1], _pos_1[2] + _z_offset*8, _pos[2], 10, 20, True)

    for i in range(8):
        _pos = add_vector_to_pos_xy(_pos, 180, 20)
        get_to_point_by_angle(_pos[0] + _offset_pos_inverse[0], _pos[1] + _offset_pos_inverse[1], _pos_1[2] + _z_offset*(8-i), _pos[2], 10, 20, True)
    return 0

### Function to measure and calculate the offset of the tip of the solder iron from the perfect centre of the flench ###
def calculate_offset_center(_posx):
    _posx[2] = 145
    movel(_posx, acc=accelleration, vel=velocity)
    _posx[2] = 80
    move_until_feedback(_posx)
    z1 = 1.825575256347656 + 108.974 # pre determant value in mm       # 1.825575256347656 is the value of hitting the table
    _pos, _i = get_current_posx() # pose in which the robot stops and take z value 
    z2 = _pos[2]
    offset = (z1-z2)/tan(45/180*3.14) + 3.70496 # calculate offset trough formula
    return offset, z2

### sometimes the robot is not that accurate so this function calculates the average offset ###
def calculate_average_offset_center(_posx):
    _offsets = []
    _z_heights = []
    for i in range(7):
        _o, _z = calculate_offset_center(get_current_posx()[0])
        _offsets.append(_o)
        _z_heights.append(_z)
    _offsets.sort()
    offset = sum(_offsets[1:-1]) / (len(_offsets) - 2)
    _z_heights.sort()
    z2 = sum(_z_heights[1:-1]) / (len(_z_heights) - 2)
    #z2 += 8        # only for the solder iron with the flat side down
    #offset -= 4
    z2 += 4        # only for the solder iron with the flat side
    offset -= 2
    return offset, z2

### function that can be called to test some lines of code ###
def test():
    get_to_point_by_angle(394.7, 415.5, 70,   0, 20, 2, True)
    get_to_point_by_angle(394.7, 415.5, 70,  90, 20, 2, True)
    get_to_point_by_angle(394.7, 415.5, 70, 180, 20, 2, True)
    get_to_point_by_angle(394.7, 415.5, 70, 270, 20, 2, True)
    return 0

### function that can be called to test some functions ###
def function_test():
    
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
offset_tolerance = 1
# end of defined variables

# start of the code
set_mode_analog_output(ch=1, mod=DR_ANALOG_VOLTAGE)  # out ch1 = voltage mode
set_analog_output(ch=1, val=0.1)

tp_popup('Lookout robot arm starts homing.', pm_type=DR_PM_MESSAGE, button_type=1)
boot_up_pos, _i = get_current_posx()
boot_up_pos[2] += 40
movel(boot_up_pos, vel=velocity, acc=accelleration)

move_home(DR_HOME_TARGET_USER)

tp_popup('Lookout robot arm starts calibrating.', pm_type=DR_PM_MESSAGE, button_type=1)
offset, z_height = calculate_average_offset_center(get_current_posx()[0])
#tp_log("offset : " + str(offset) + " , z height : " + str(z_height))
move_home(DR_HOME_TARGET_USER)

one_time_flag = True
while True:
    tp_popup('Start new soldering job?', pm_type=DR_PM_MESSAGE, button_type=0)
    if(one_time_flag):
        one_time_flag = False
    else:
        tp_popup('Lookout robot arm checks calibration.', pm_type=DR_PM_MESSAGE, button_type=1)
        _check_offset, _check_z_height = calculate_offset_center(get_current_posx()[0])
        move_home(DR_HOME_TARGET_USER)
        tp_log(str(abs(offset - _check_offset) > offset_tolerance))
        if(abs(offset - _check_offset) > offset_tolerance):
            tp_popup('Needs to recalibrate! Lookout robot arm starts calibrating.', pm_type=DR_PM_MESSAGE, button_type=1)
            offset, z_height = calculate_average_offset_center(get_current_posx()[0])
            move_home(DR_HOME_TARGET_USER)
            tp_popup('Continue soldering job?', pm_type=DR_PM_MESSAGE, button_type=0)

    #test()
    #function_test()
    soldeer()
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
