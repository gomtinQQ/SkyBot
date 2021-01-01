import sys, os
import datetime, time
import pandas as pd
import multiprocessing as mp
from multiprocessing import Process, Queue

from XASessions import *
from XAQueries import *
from XAReals import *

class RealTimeWorker(mp.Process):

    def __init__(self, dataQ):
        super(RealTimeWorker, self).__init__()

        self.daemon = True

        self.dataQ = dataQ

        self.connection = None

        # 실시간요청 아이디 초기화
        self.JIF = None

        self.YJ = None
        self.YFC = None
        self.YS3 = None
        self.YOC = None

        self.FUT_REAL_FC0 = None
        self.FUT_HO_FH0 = None
        self.OPT_REAL_OC0 = None  
        self.OPT_HO_OH0 = None

        self.FUT_REAL_NC0 = None
        self.FUT_HO_NH0 = None
        self.OPT_REAL_EC0 = None  
        self.OPT_HO_EH0 = None  

        self.IJ = None
        self.S3 = None
        self.BM = None
        self.PM = None

        self.OVC = None
        self.OVH = None
        self.WOC = None
        self.NWS = None

        self.exit = mp.Event()

    def OnLogin(self, code, msg):

        if code == '0000':

            # 로그인 이후 객체를 생성해야 됨
            self.JIF = JIF(parent=self)

            self.YJ = YJ_(parent=self)
            self.YFC = YFC(parent=self)
            self.YS3 = YS3(parent=self)
            self.YOC = YOC(parent=self)
            
            self.FUT_REAL_FC0 = FC0(parent=self)
            self.FUT_HO_FH0 = FH0(parent=self)
            self.OPT_REAL_OC0 = OC0(parent=self)
            self.OPT_HO_OH0 = OH0(parent=self)

            self.FUT_REAL_NC0 = NC0(parent=self)
            self.FUT_HO_NH0 = NH0(parent=self)
            self.OPT_REAL_EC0 = EC0(parent=self)
            self.OPT_HO_EH0 = EH0(parent=self)

            self.IJ = IJ_(parent=self)
            self.S3 = S3_(parent=self)
            self.BM = BM_(parent=self)
            self.PM = PM_(parent=self)

            self.OVC = OVC(parent=self)
            self.OVH = OVH(parent=self)
            self.WOC = WOC(parent=self)

            self.NWS = NWS(parent=self)

            print('로그인 성공...')

            self.NWS.AdviseRealData()
        else:
            print('로그인 실패...')

    def OnLogout(self):

        print("로그아웃 되었습니다.")

    def OnDisconnect(self):

        print("연결이 끊겼습니다.")

    def OnReceiveMessage(self, ClassName, systemError, messageCode, message):

        txt = 'ClassName = {0} : systemError = {1}, messageCode = {2}, message = {3}'.format(ClassName, systemError, messageCode, message)
        print(txt)
    
    def OnReceiveData(self, szTrCode, result):

        print(result)

    def OnReceiveRealData(self, szTrCode, result):

        print(result)
        self.dataQ.put(result, False)
    
    def login(self):

        계좌정보 = pd.read_csv("secret/passwords.csv", converters={'계좌번호': str, '거래비밀번호': str})

        주식계좌정보 = 계좌정보.query("구분 == '모의'")
        print('모의서버에 접속합니다.') 

        self.connection = XASession(parent=self)

        self.url = 주식계좌정보['url'].values[0].strip()
        self.id = 주식계좌정보['사용자ID'].values[0].strip()
        self.pwd = 주식계좌정보['비밀번호'].values[0].strip()
        self.cert = 주식계좌정보['공인인증비밀번호'].values[0].strip()
        
        self.connection.login(url=self.url, id=self.id, pwd=self.pwd, cert=self.cert)        

    def run(self):

        print('MultiProcessing RealTimeWorker Start...')

        while not self.exit.is_set():
            pass

        print("MultiProcessing RealTimeWorker Terminated !!!")

    def shutdown(self):

        print("MultiProcessing Shutdown initiated...")
        
        print('실시간요청 취소...')
        self.NWS.UnadviseRealData()

        print('서버연결 해지...')
        self.connection.disconnect()

        self.exit.set()            