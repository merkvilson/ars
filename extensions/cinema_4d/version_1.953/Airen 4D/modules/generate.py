from airen_paths import *
from plugin_ids  import *
from airen_cmds  import *
import c4d
import subprocess
import threading
import time
import socket
import json
import base64
import re
import shutil
import os
import random
__DEBUG__ = True



def tcp_request(ip, port, message, response_list):
    try:
       
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, port)) # Connect to the server

        if __DEBUG__:  print(f"[tcp_reques] before sendall='{message}'")


        client_socket.sendall(message.encode())     # Send a message to the server
        response = client_socket.recv(1024).decode()# Receive the response from the server
        client_socket.close()                       # Close the connection
        
        if __DEBUG__:print(f"[tcp_reques] recv='{response}'")
        digit_status = re.sub(r'\D', '', response) 
        c4d.StatusSetText(f"Starting Airen Engine: {digit_status}")

        response_list.append(response)
        return True



    except Exception as e:
        if __DEBUG__:print(f"[tcp_reques] : Failed to send message: '{message}' to 'file_path'\nTo address {ip}:{port}")
        if __DEBUG__:print(f"[tcp_reques] : Error code: {e}")

    if __DEBUG__:print(f"[tcp_reques] : return False")
    return False


def tcp_request2(ip, port, message, response_list):
    try:
       
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, port)) # Connect to the server

        if __DEBUG__:  print(f"[tcp_reques] before sendall='{message}'")


        client_socket.sendall(message.encode())     # Send a message to the server
        response = client_socket.recv(1024).decode()# Receive the response from the server
        client_socket.close()                       # Close the connection
        
        if __DEBUG__:print(f"[tcp_reques] recv='{response}'")
        digit_status = re.sub(r'\D', '', response) 
        c4d.StatusSetText(f"Starting Airen Engine: {digit_status}")

        response_list.append(response)
        return True



    except Exception as e:
        if __DEBUG__:print(f"[tcp_reques] : Failed to send message: '{message}' to 'file_path'\nTo address {ip}:{port}")
        if __DEBUG__:print(f"[tcp_reques] : Error code: {e}")

    if __DEBUG__:print(f"[tcp_reques] : return False")
    return False








def update_progress_bar(fValue, node, status_text) :
    
    text = f"00{int(fValue * 100)}%"[-4:]

    status_progress = int(fValue * 100)
    status_progress=round(c4d.utils.RangeMap(value=status_progress, mininput=0, maxinput=100, minoutput=0, maxoutput=99, clampval=True),1)
    c4d.StatusSetBar(status_progress)
    c4d.StatusSetText(f'{status_progress}% {status_text}')

    if node: 
        node[1007] = f"   {text}   "
        node[1008] = status_progress

    
    c4d.EventAdd()




def tcp_request_while(ip, port, message, response_list, node, status_text):
    if __DEBUG__:print(f"[tcp_request_whil] : ")
    try:
        # Connect to the server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, port))
        
        # Send a message to the server
        if __DEBUG__:print(f"[tcp_request_whil] before sendall='{message}'")

        client_socket.sendall(message.encode())
        
        while True:
            # Receive the response from the server
            response = client_socket.recv(1024).decode()

            if __DEBUG__:print(f"[tcp_request_whil] response={response}")

            if not response:
                if __DEBUG__:print(f"[tcp_request_whil] AHTUNG! Connection closed by the server.")
                break


            if "MESH_SAVED_SUCCESSFULLY" in response:
                node[GENERATE_BUTTON] = True
                node[GENERATE_OBJ3D] = True
                saved_mesh = os.path.join(sd_3d_dir, '0', 'mesh.obj')
                import_obj(saved_mesh)  
                for obj in c4d.documents.GetActiveDocument().GetObjects():
                    if obj.GetName() == 'Default':
                        obj.SetName(f'OBJ_{time.time()}')
                        material = obj.GetTag(c4d.Ttexture)[c4d.TEXTURETAG_MATERIAL]
                        material[c4d.MATERIAL_USE_COLOR] = False
                        material[c4d.MATERIAL_USE_REFLECTION] = False
                        material[c4d.MATERIAL_USE_LUMINANCE] = True
                        material[c4d.MATERIAL_LUMINANCE_SHADER] = material[c4d.MATERIAL_COLOR_SHADER]
                        obj.InsertUnder(node)
                        bbox = obj.GetRad()
                        height = bbox.y * 2
                        new_axis_pos = c4d.Vector(0, height/2, 0)
                        obj.SetAbsPos(new_axis_pos)
                        obj.DelBit(c4d.BIT_ACTIVE)
                        node.SetBit(c4d.BIT_ACTIVE)

                break



            if "IMAGE_SAVED_SUCCESSFULLY" in response:

                # Используем регулярное выражение для поиска текста после ключевого маркера
                match = re.search(r'IMAGE_SAVED_SUCCESSFULLY:(.+)', response)

                # Проверяем, был ли найден текст после ключевого маркера
                if True:
                    c4d.StatusClear()
                    #saved_image_path = os.path.join(dir,os.listdir(dir)[-1])
                    saved_image_path = response[len('IMAGE_SAVED_SUCCESSFULLY: '):]                                
                    
                    if node: 
                        if node.GetType() in [AI_SKY, AI_BG]:
                            node.GetDown().GetTag(c4d.Ttexture)[c4d.TEXTURETAG_MATERIAL][c4d.MATERIAL_LUMINANCE_SHADER][c4d.BITMAPSHADER_FILENAME] = saved_image_path
                            c4d.EventAdd()

                        #c4d.CallButton(node, REMOVE_BG)

                        node[IMAGE_PATH] = saved_image_path

                        node[GENERATE_BUTTON] = True
                        node[GENERATE_OBJ3D] = True
                        node[1007] = "Start..."
                        node.SetDirty(c4d.DIRTYFLAGS_ALL)
                        #node.SetAbsPos(c4d.Vector(0,(random.randint(0,1000))/100,0))
                        c4d.EventAdd()
                    
                    else:
                        c4d.EventAdd()
                        print("Airen Rendering Finished")
                #else: if __DEBUG__:print(f"[tcp_request_whil] : ERROR! ")
                
                break
        
            if response == "IMAGE_GENERATION_PROCESS_STARTED":
                if __DEBUG__:print(f"[tcp_request_whil] : IMAGE_GENERATION_PROCESS_STARTED")
            elif response == "Connection refused": 
                c4d.gui.MessageDialog(f"Airen can't start. \nPlease report the bug.")
                break
            elif response == "OK_RECOV_START_TCP_SEVER": 
                if __DEBUG__:print(f"[tcp_request_whil] str610 ok")
            elif "PROGRESS_TXT2IMG" in response:
                # Split the response string to get the progress value after ":"
                progress_value = response.split(":")[1]
                try:
                    # Convert the progress value to a float
                    progress_value = float(progress_value)
                    update_progress_bar(progress_value, node, status_text)
                except ValueError:
                    if __DEBUG__:print(f"[tcp_request_whil] Error parsing progress value as float. | break")
                    break
            elif "STARTUP_PROCESS_RUNBAT" in response:
                # Split the response string to get the progress value after ":"
                progress_value = response.split(":")[1]
                try:
                    # Convert the progress value to a float
                    progress_value = float(progress_value)
                    update_progress_bar(progress_value, node, status_text)
                except ValueError:
                    if __DEBUG__:print(f"[tcp_request_whil] str628 Error parsing progress value as float. | break")
                    c4d.gui.MessageDialog(f"str 629: Error parsing progress value as float. | break")
                    break

            elif "SD_MODEL_CHECKPOINT_FINISHED" in response:
                ret_code = response.split(":")[1]
                try:
                     # Convert the progress value to an integer
                    ret_code = int(ret_code)
                    if ret_code != 0:
                        c4d.gui.MessageDialog(f"failed to change model")
                    break
                except ValueError:
                    c4d.gui.MessageDialog("Error parsing progress value as int. Please check your input.")
                    break

            elif "SD_MODEL_CHECKPOINT_PROCESS_STARTED" in response:
                print("the server has started the process of loading a new model")

            elif "OK_TRIPROSR" in response:
                node[GENERATE_OBJ3D] = False
                if __DEBUG__:print(f"[tcp_request_whil] сервер начал генерацию меша")

            else:
                if __DEBUG__:print(f"[tcp_request_whil] str 695: СЕРВЕР ПРИСЛАЛ ХЕРНЮ. КРИТИЧЕСКАЯ ОШИБКА")


        if __DEBUG__:print(f"[tcp_request_whil] before close tcp")

        # Close the connection
        client_socket.close()

        response_list.append(response)
        return True
    except Exception as e:
        if __DEBUG__:print(f"[tcp_request_whil] : Failed to send message: '{message}' to 'file_path' To address {ip}:{port}\n[tcp_request_whil] : Error code: {e}")

    return False




def run_systray_gui():
    try:
        os.chdir(airen_root_path)

        if __DEBUG__:print(f"[run_systray_gu] : call {sd_airen_exe_path}")
        process = subprocess.Popen([sd_airen_exe_path], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(1)
        # c4d.gui.MessageDialog(f"str 655: wait for run qt_gui.exe")
               
        return True
    except Exception as e:
        if __DEBUG__:print(f"[run_systray_gu] : Error occurred - {e}")
        return False






def request_start_run_bat():
    # на этом этапе exe микросервис находется процессе запуска
    # мы отправим ему сообщение REQUEST_TO_RUN_RUNBAT и будем 
    # ожидать в ответ OK_RECOV_START_TCP_SEVER что означает что
    # что exe утилита  попыталась запустить в свою очередь stablediffusion bat
    cnt = 10
    for i in range(cnt):
        response_container = []
        if __DEBUG__:print(f"[request_start_run_ba] [for] : step {i}/{10}")
        result = tcp_request("127.0.0.1", 20837, "REQUEST_TO_RUN_RUNBAT", response_container)
        
        if result:
            server_response = response_container[0]

            if server_response == "OK_RECOV_START_TCP_SEVER":
                break
            else:
                if __DEBUG__:print(f"[request_start_run_ba] [for] : str701 ждём когда запустится графическая оболочка exe")
                time.sleep(1.0)
        else:
            if __DEBUG__:print(f"[request_start_run_ba] [for] : str705 ждём когда запустится графическая оболочка exe")
            time.sleep(1.0)




def click_generate_button(node, final_p, status_text, dir):

    c4d.StatusSetSpin()

    delete_all_files_in_folder(sd_steps_path)


    if node: 
        node[GENERATE_BUTTON] = False
        node[GENERATE_OBJ3D] = True


    class server_thread(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)

        def run(self):  

          

            # Проверяем запущена ли графическая оболочка
            # ----------------------------------------------------------------------------------------------
            response_container = []
            result = tcp_request("127.0.0.1", 20837, "MSG_PING_SYSTRAY_GUI", response_container) # test

            if result:
                server_response = response_container[0]
                if __DEBUG__:print(f"[generate clicked] : Server response: {server_response}")

                # Добавляем проверку на тип ответа. 
                if server_response == "MSG_PING_SYSTRAY_GUI":
                    if __DEBUG__:print("[generate clicked] : detect  MSG_PING_SYSTRAY_GUI response.")
                else:
                    if __DEBUG__:print(f"[generate clicked] : str692 UNKNOW ANSWER: {server_response}")
                    return
            else:
                if __DEBUG__:print("str733 | Failed to connect to the server. | Графическая оболочка не запущена! |  дальше будет попытка запуска exe микросервиса")
                if run_systray_gui() == True :
                    request_start_run_bat()


            # Проверяем запущен ли STABLEDIFFUSION от AUTOMATIC1111
            # ----------------------------------------------------------------------------------------------
            while True: 
                response_container = []
                result = tcp_request("127.0.0.1", 20837, "MSG_IS_STABLEDIFFUSION_RUNNING", response_container)
                
                
                if result:
                    server_response = response_container[0]


                    if server_response == "RESPONSE_STABLEDIFFUSION_OFF":
                        if __DEBUG__:print("[generate clicked] [While] : TODO отправить запрос на запуск стэйбла")
                        return
                    elif server_response == "STABLE_DIFFUSION_WORK":
                        if __DEBUG__:print("[generate clicked] [While] : ")
                        break
 
                    elif server_response == "STABLE_DIFFUSION_NOT_WORK":
                        if __DEBUG__:print("[generate clicked] [While] : TODO отправить запрос на запуск стэйбла | before call request_start_run_bat ")
                        request_start_run_bat()

                    elif server_response == "RESPONSE_STABLEDIFFUSION_ON":
                        # STABLEDIFFUSION ЗАПУЩЕН. 
                        if __DEBUG__:print("[generate clicked] [While] : ok RESPONSE_STABLEDIFFUSION_ON | окей стэйбл ожидает промт для генерации | останавливаем цикл while | ниже по коду должна произойти отправка promt ")
                        break

                    elif server_response == "STABLE_DIFFUSION_RUNTIME_ERRORS":
                        # STABLEDIFFUSION ЗАПУЩЕН 
                        if __DEBUG__:print("Stable is not running correctly")
                        break

                    elif "STABLE_DIFFUSION_LAUNCH_PROCESS" in server_response:
                        # сервер прислал кусочек фэйкового прогресс бара первых этапов старт стэйбла
                        # Split the response string to get the progress value after ":"
                        time.sleep(1)
                        progress_value = server_response.split(":")[1]
                        try:
                            # Convert the progress value to a float
                            progress_value = float(progress_value)

                            if __DEBUG__:print(f"[generate clicked] [While]  {progress_value}" )
                            
                        except ValueError:
                            if __DEBUG__:print("[generate clicked] str750 Критическая ошибка! " )
                            break
                    else:
                        if __DEBUG__:print(f"[generate clicked] str764 unknow answer: {server_response}")
                        break

                else:
                    if __DEBUG__:print("[generate clicked]  str788 | графическая оболочка systray упала?! ")
                    return


            # Sending Request For IMG Generqation

            if final_p:
                response_container = []
                payload_json = json.dumps(final_p)
                encoded_payload = base64.b64encode(payload_json.encode('utf-8'))

                decoded_payload = encoded_payload.decode('utf-8')


                prompt = "prompt: " + decoded_payload
                if "init_images" in final_p: prompt = "img2img: " + decoded_payload
                elif "sd_model_checkpoint" in final_p: prompt = "sd_model_checkpoint: " + decoded_payload
                elif "rembg" in final_p: prompt = "rembg: " + decoded_payload

            else:
                "prompt: " + ''

            tcp_request_while("127.0.0.1", 20837, prompt, response_container, node, status_text)

            if result:
                server_response = response_container[0]
                if __DEBUG__:print(f" ok ? ")
            else:
                if __DEBUG__:print("Failed to connect to the server. | Графическая оболочка не запущена!")
                return

    server_thread().start()
