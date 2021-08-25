from datetime import datetime
import pythoncom
import math
import time
import multiprocessing as mp
from multiprocessing import Queue
from configparser import ConfigParser

from xing_config import *
from xing_api import *
from xing_utils import * 
from xing_option_tick_real_time import *

make_dir(TICKER_DATA_FOLDER_PATH)
TODAY = datetime.today().strftime("%Y-%m-%d")
TODAY_PATH = f"{TICKER_DATA_FOLDER_PATH}/{TODAY}"
make_dir(TODAY_PATH)

# Configuration Parser
parser = ConfigParser()
parser.read('.\skybot.ini')

REAL_SERVER = parser.getboolean('Server Type', 'Real Server')
OPTION_SLEEP_SWITCH_MODE = parser.getboolean('User Switch', 'MP Option Sleep Switching Mode')
OPTION_SLEEP_SWITCHING_DELAY = parser.getfloat('Initial Value', 'MP Option Sleep Switching Delay')
YOC_REQUEST = parser.getboolean('User Switch', 'YOC Request')

계좌정보 = pd.read_csv("secret/passwords.csv", converters={'계좌번호': str, '거래비밀번호': str})

if REAL_SERVER:
    주식계좌정보 = 계좌정보.query("구분 == '거래'")
    print('MP 실서버에 접속합니다.')

    ID = 주식계좌정보['사용자ID'].values[0].strip()            
    PWD = 주식계좌정보['비밀번호'].values[0].strip()
    CERT = 주식계좌정보['공인인증비밀번호'].values[0].strip()

    is_real_server = True
    config = {"id": ID, "password": PWD, "cert_password": CERT}
else:
    주식계좌정보 = 계좌정보.query("구분 == '모의'")
    print('MP 모의서버에 접속합니다.')

    ID = 주식계좌정보['사용자ID'].values[0].strip()            
    PWD = 주식계좌정보['비밀번호'].values[0].strip()
    CERT = 주식계좌정보['공인인증비밀번호'].values[0].strip()

    is_real_server = False
    config = {"id": ID, "password": PWD, "cert_password": "0"}

def option_tick_crawler(queue: Queue, index_option_cm_tick=False, index_option_nm_tick=False):

    proc = mp.current_process()
    print(f'\r지수옵션 체결 Process Name = {proc.name}, Process ID = {proc.pid}')
                          
    result = XingAPI.login(config["id"], config["password"], config["cert_password"], is_real_server)
    result.append('지수옵션체결')

    queue.put(result)

    if result[0] == 'login' and result[1] == '0000':

        # ################################# 지수선물 근월물, 차월물 선물코드 ############################################
        gmshcode, cmshcode = XingAPI.get_index_futures_gm_cm_code()
        # ############################################################################################################
        
        # ################################# t2101 요청 ################################################################
        t2101_df = XingAPI.t2101(gmshcode)
        kp200 = float(t2101_df.at[0, 'KOSPI200지수'])

        temp = math.floor(round(kp200 / 2.5, 0) * 2.5)
        atm_txt = '{0:.0f}'.format(temp)        

        print('kp200 지수 =', kp200, atm_txt)
        # ############################################################################################################        

        # ################################# 지수옵션 ##################################################################
        listed_code_df, cm_call_code_list, cm_put_code_list, nm_call_code_list, nm_put_code_list = XingAPI.get_index_option_listed_code_list()
        listed_code_df.to_csv(f"{TODAY_PATH}/index_option_listed_code.csv", encoding='utf-8-sig')

        cm_code_list = cm_call_code_list + cm_put_code_list
        nm_code_list = nm_call_code_list + nm_put_code_list

        # 체결
        if index_option_cm_tick:

            if YOC_REQUEST:
                print('본월물 실시간 예상체결 요청...')
                real_time_index_option_yoc_tick = RealTimeIndexOptionYOCTick(queue=queue)
                real_time_index_option_yoc_tick.set_code_list(cm_code_list, field="optcode")
            else:
                pass

            print('본월물 실시간 체결요청...')
            real_time_index_option_tick = RealTimeIndexOptionTick(queue=queue)
            real_time_index_option_tick.set_code_list(cm_code_list, field="optcode")

        if index_option_nm_tick:

            if YOC_REQUEST:
                print('차월물 실시간 예상체결 요청...')
                real_time_index_option_yoc_tick = RealTimeIndexOptionYOCTick(queue=queue)
                real_time_index_option_yoc_tick.set_code_list(nm_code_list, field="optcode")
            else:
                pass
            
            print('차월물 실시간 체결요청...')
            real_time_index_option_tick = RealTimeIndexOptionTick(queue=queue)
            real_time_index_option_tick.set_code_list(nm_code_list, field="optcode")
        # ############################################################################################################

        while True:
            pythoncom.PumpWaitingMessages()

            if OPTION_SLEEP_SWITCH_MODE:
                time.sleep(OPTION_SLEEP_SWITCHING_DELAY)
    else:
        pass
