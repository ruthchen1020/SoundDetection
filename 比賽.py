import matplotlib.pyplot as plt
import numpy as np
import pyaudio
import math
import struct
import time
import csv
from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.fftpack import fft

class AudioStream(object):
    def __init__(self):                           # 常數
        
        self.CHUNK = 1024 * 2                     # 每幀樣本數
        self.FORMAT = pyaudio.paInt16             # 樣本格式
        self.CHANNELS = 1                         # 聲道數量
        self.RATE = 44100                         # 一秒的樣本數
        self.pause = False                        # 停止變數
        self.frames = []                          # 紀錄數據list
        self.p = pyaudio.PyAudio()                # 建立 pyaudio 物件
        self.filename = "record.csv"              # 數據紀錄處
        self.max = 0                              # 最大值
        self.warning_db = 80                       # 分貝上限(警告用)
        self.warning_freq = 1000                   # 頻率上限(警告用)
        self.frame_count = 0                      # 數幀數

        self.root = Tk()                          # 創建窗口
        self.canvas = Canvas()                      # 創建顯示圖形的畫布
        self.figure = self.create_matplotlib()      # 返回matplotlib所畫圖形的figure對象
        self.create_form(self.figure)             # 將figure顯示在tkinter視窗上面
        
        self.stream = self.p.open(                # 從麥克風中獲取音訊數據
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            output=True,
            frames_per_buffer=self.CHUNK          # 每一個buffer中的幀數
        )
        self.start_stream()                       # 開始錄音加畫圖
        self.root.mainloop()

    # matplot initiall setting
    def create_matplotlib(self):
        # 創建繪圖對象f&兩個子圖
        self.f = plt.figure(figsize=(160,120), dpi = 100)
        self.ax = self.f.add_subplot(2,1,1)                                 
        self.ax2 = self.f.add_subplot(2,1,2)
        
        ##分貝圖xy軸範圍
        self.ax.set_ylim(0,100)
        self.ax.set_xlim(1,2048)
        ##頻率圖xy軸範圍
        self.ax2.set_ylim(0,10)
        self.ax2.set_xlim(20,20000)

        ##標題&xy軸標題設定
        self.ax.set_title('AUDIO WAVEFORM')
        self.ax.set_xlabel('samples')
        self.ax.set_ylabel('volume(DB)')
        self.ax2.set_xlabel('frequency(Hz)')
        self.ax2.set_ylabel('strength')

        # 計算時間
        self.start_time = time.time()      # 紀錄開始時間

        # matplot回傳
        return self.f
        
    ##繪製數據
    def create_form(self,figure):
        button = Button(master=self.root, text="Quit", command=self.quit)
        button.pack(side=RIGHT,ipadx=50)
        
        #初始化數據線
        x = np.arange(0,self.CHUNK)                                     # x的數值
        xf = np.linspace(0, self.RATE, self.CHUNK)
        self.line, = self.ax.plot(x,np.random.rand(self.CHUNK),'r')     # 先隨機出一條線
        self.line2, = self.ax2.plot(xf,np.random.rand(self.CHUNK),'b')
        
        #把繪製的圖形(數據)顯示到tkinter視窗上
        self.canvas=FigureCanvasTkAgg(figure,self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=BOTTOM)

    # 開始錄音加畫圖
    def start_stream(self):  
        print('stream started')               # 開始錄音
        # 把繪製的圖形顯示到tkinter窗口上
        while not self.pause :  
            #數據擷取&處理
            data = self.stream.read(self.CHUNK)                                         # 讀取stream資料
            data_int = struct.unpack(str(self.CHUNK) + 'h', data)                       # byte to interger
            data_dB = [20 * math.log10(abs(x)) if x != 0 else 0 for x in data_int]      # 轉換為分貝
            yf = np.abs(fft(data_int)[0:self.CHUNK])/ (128 * self.CHUNK)
            
            #分貝&頻率的y軸數據畫成線
            self.line.set_ydata(data_dB)                                   
            self.line2.set_ydata(yf)
            
            #丟到圖上
            self.canvas.draw()                   # 畫在canvas畫布fig圖上
            self.canvas.flush_events()           # 刷新畫布
            self.frames.append(list(data_dB))

            #若分貝>設定上限則 warning
            if max(data_dB) > (self.warning_db):  # 若分貝大於設定上限
                self.warning('volume',max(data_dB))                   
            if max(yf) > (self.warning_freq):     # 若頻率大於設定上限
                self.warning('frequency',max(yf))
        else:    
            self.exit_app()                       # 當停止時，呼叫exit_app
    
    # 離開app
    def exit_app(self):                                 
        self.p.close(self.stream)                       # 關閉麥克風
        print('stream closed')                          # 提示字元
        self.find_max()                                 # 找最大值
        self.write()                                    # 寫入檔案
        self.root.quit()
        self.root.destroy()

    # 找最大值函數
    def find_max(self):                                     # 找最大值函數
        self.max= max(max(sig) for sig in self.frames)      # 用for找二維list
        print("max vol(dB) = ",self.max)                    # 提示字元

    # 警告函數
    def warning(self,volordb,val):
        t = time.time() - self.start_time                   # 經過秒數
        print(f"warning,{volordb}={val},time={t:.4f}")                      # 警告字元

    #寫檔函數
    def write(self):
        wf = open(self.filename, 'w')                       # 讀寫聲音記錄檔
        writer = csv.writer(wf)                             # 使用csv.writer()建立一個csv寫入器
        writer.writerows(self.frames)                       # writer.writerows()將二維list中的每一個子list寫入到檔案
        wf.close()                                          # 關掉檔案
        print("file has been saved")                        # 資料寫入提示

    # 點一下結束
    def quit(self):
        self.pause = True                                   # 停止參數=True

    
if __name__ == '__main__':                      
    AudioStream()