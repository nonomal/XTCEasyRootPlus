import subprocess
import sys
import requests
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.console import Console
from urllib import parse
from time import sleep
import time
import serial.tools.list_ports
from rich.table import Table
import zipfile
import os
import re
import shutil
import rich.status
from patch_boot import patch



class Log:
    def __init__(self):
        if not os.path.exists('logs/'):
            os.mkdir('logs')
        self.logname = f'logs/{time.strftime("%Y_%m_%d_%H-%M-%S", time.localtime())}.log'
    def run_wait(self,args: str,returncode=False):
        """
        运行一个程序并等待
        args: string;command line
        return
        """
        with open(self.logname,'a') as f:
            f.write(f'>>>{args}\n')
        p = subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=False)
        if returncode:
            with open(self.logname,'a') as f:
                f.write(f'return {p.returncode}')
            return p.returncode
        else:
            try:
                stdout = p.stdout.decode()
                with open(self.logname,'a') as f:
                    f.write(f'{stdout}\n\n')
            except UnicodeDecodeError:
                stdout = p.stdout
                with open(self.logname,'ab') as f:
                    f.write(stdout)
                with open(self.logname,'a') as f:
                    f.write('\n\n')
            return stdout
    def logging(self,log):
        with open(self.logname,'a') as f:
            f.write(f'log>{log}\n\n')

_log = Log()
run_wait = _log.run_wait
logging = _log.logging

def clear_line():
    print('\r',end='')
    for i in range(20):
        print(' ',end='')
    print('\r',end='')

def exit_after_enter():
    input('')
    sys.exit()

def download_file(url: str, filename: str = '', progress: bool = True):
    if filename == '':
        filename = parse.unquote(url.split('/')[-1].split('&')[0])
    
    if progress:
        with Progress(
            TextColumn(f"[bold blue]下载文件\"{filename.split('/')[-1]}\":"),  # 提示文字
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            "[green]{task.completed} / {task.total} KB",
            "•",
            TimeRemainingColumn(),
        ) as progress:
            # 发起 HTTP 请求，流式获取内容
            with requests.get(url, stream=True) as r:
                # 获取文件总大小
                total_size = round(int(r.headers.get('content-length', 0))/1024)
                # 在进度条中创建一个任务
                task_id = progress.add_task("download", total=total_size)
                # 打开文件以写入
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):  # 每次读取 1KB
                        if chunk:  # 确保读取的内容非空
                            f.write(chunk)
                            # 更新进度条
                            progress.update(task_id, advance=round(len(chunk)/1024))
    else:
        with requests.get(url, stream=True) as r:
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):  # 每次读取 1KB
                    if chunk:  # 确保读取的内容非空
                        f.write(chunk)

def print_logo(version):
    logo = r'''[#01BFEE] __   _________ _____ ______                _____             _   _____  _           
 \ \ / /__   __/ ____|  ____|              |  __ \           | | |  __ \| |          
  \ V /   | | | |    | |__   __ _ ___ _   _| |__) |___   ___ | |_| |__) | |_   _ ___ 
   > <    | | | |    |  __| / _` / __| | | |  _  // _ \ / _ \| __|  ___/| | | | / __|
  / . \   | | | |____| |___| (_| \__ \ |_| | | \ \ (_) | (_) | |_| |    | | |_| \__ \
 /_/ \_\  |_|  \_____|______\__,_|___/\__, |_|  \_\___/ \___/ \__|_|    |_|\__,_|___/
                                       __/ |                                         
                                      |___/                                          '''
    console = Console()
    print = console.print
    logo = logo[0:-(len(str(version[0]))+len(str(version[1]))+2)]
    logo = logo+f'[/#01BFEE][blue]v{version[0]}.{version[1]}[/blue]'
    print(logo)

class ADB:
    def __init__(self,path) -> None:
        self.path = path
    def adb(self,input):
        return run_wait(f'{self.path} {input}')
    def is_connect(self):
        output = self.adb('devices')
        return '\tdevice' in output
    def wait_for_connect(self,sleep_time=0.5):
        while True:
            if self.is_connect():
                break
            sleep(sleep_time)
    def get_innermodel(self):
        return self.adb('shell getprop ro.product.innermodel').replace('\n','').replace('\r','')
    def get_model(self):
        return self.adb('shell getprop ro.product.model').replace('\n','').replace('\r','')
    def get_version_of_android(self):
        return self.adb('shell getprop ro.build.version.release').replace('\n','').replace('\r','')
    def get_version_of_system(self):
        return self.adb('shell getprop ro.product.current.softversion').replace('\n','').replace('\r','')
    def get_info(self):
        output = {'innermodel': self.get_innermodel(), 'model': self.get_model(),
                  'version_of_android': self.get_version_of_android(),
                  'version_of_system': self.get_version_of_system(),
                  'version_of_android_from_sdk': self.get_version_of_android_from_sdk()}
        return output
    def get_plmnstatus(self):
        return self.adb('shell getprop gsm.xtcplmn.plmnstatus')
    def install(self,path: str,args=['r','t','d']):
        argsstr = ''
        for i in args:
            argsstr = argsstr + '-' + i + ' '
        while True:
            output = self.adb(f'install {argsstr}"{path}"')
            if 'Success' in output:
                break
            elif 'Broken pipe' in output:
                self.wait_for_connect()
                continue
            else:
                break
        if 'Success' in output:
            return 'success'
        else:
            return output
    def shell(self,shell):
        return self.adb(f'shell {shell}')
    def xtc_is_v3(self):
        if 'true' in self.shell('getprop persist.sys.isv3'):
            return True
        else:
            return False
    def push(self,input,path):
        self.adb(f'push "{input}" "{path}"')
    def install_module(self,path):
        self.push(path,'/sdcard/temp_module.zip')
        self.shell('"echo -e \'chmod 777 /data/adb/magisk/busybox\\nDATABIN=\\"/data/adb/magisk\\"\\nBBPATH=\\"/data/adb/magisk/busybox\\"\\nUTIL_FUNCTIONS_SH=\\"$DATABIN/util_functions.sh\\"\\nexport OUTFD=1\\nexport ZIPFILE=\\"/sdcard/temp_module.zip\\"\\nexport ASH_STANDALONE=1\\n\\"$BBPATH\\" sh -c \\". \\\\\\"$UTIL_FUNCTIONS_SH\\\\\\"; install_module\\"\' > /sdcard/temp_module_installer.sh"')
        output = self.shell(r'su -c "sh /sdcard/temp_module_installer.sh"')
        self.shell('rm -rf /sdcard/temp_module.zip')
        return output
    def install_module_new(self,path):
        self.push(path,'/sdcard/temp_module.zip')
        output = self.shell('su -c magisk --install-module /sdcard/temp_module.zip')
        self.shell('rm -rf /sdcard/temp_module.zip')
        return output
    def wait_for_complete(self,sleep_time=0.5):
        while True:
            output = self.shell('getprop sys.boot_completed')
            if '1' in output:
                break
            sleep(sleep_time)
    def get_activity(self):
        output = self.shell('"dumpsys window | grep mTopFullscreenOpaqueWindowState | sed \'s/ /\\n/g\' | tail -n 1 | sed \'s/\\/.*$//g\'"')
        return output
    def get_version_of_sdk(self):
        return self.shell('getprop ro.build.version.sdk').replace('\n','').replace('\r','')
    def get_version_of_android_from_sdk(self):
        sdk = self.get_version_of_sdk()
        return {
            '9': '2.3',
            '10': '2.3.3',
            '11': '3.0',
            '12': '3.1',
            '13': '3.2',
            '14': '4.0',
            '15': '4.0.3',
            '16': '4.1',
            '17': '4.2',
            '18': '4.3',
            '19': '4.4',
            '20': '4.4W',
            '21': '5.0',
            '23': '6.0',
            '24': '7.0',
            '25': '7.1',
            '26': '8.0',
            '27': '8.1',
            '28': '9',
            '29': '10',
            '30': '11',
            '31': '12',
            '32': '12',
            '33': '13',
            '34': '14',
            '35': '15'
        }[sdk]
    def is_xtc(self):
        innermodel = self.get_innermodel()
        return innermodel in list(xtc_models.keys())
    def is_screen_alive(self):
        output = self.shell('dumpsys display | grep mState')
        return 'mState=ON' in output

def check_edl():
    for port in serial.tools.list_ports.comports():
        if 'Qualcomm' in port.description and '9008' in port.description:
            return port.device[3:]
    return False

def wait_for_edl(sleeptime=0.5):
    while True:
        check = check_edl()
        if not check == False:
            return check.replace('\n','').replace('\r','')
        sleep(sleeptime)

def print_error(title,content):
    logging(f'错误:{title}')
    console = Console()
    print = console.print
    table = Table()
    table.add_column(f'错误:{title}')
    table.add_row(content)
    print(table)

class QT:
    def __init__(self,qsspath,fhlpath,port,mbn,emmcdlpath='bin/emmcdl.exe') -> None:
        self.qsspath = qsspath
        self.fhlpath = fhlpath
        self.port = port
        self.mbn = mbn
        self.emmcdlpath = emmcdlpath
    
    def intosahara(self):
        output = run_wait(f'{self.qsspath} -u {str(self.port)} -s 13:"{self.mbn}"')
        if type(output) == str:
            if not 'Sahara protocol completed' in output:
                return output
            else:
                return 'success'
        else:
            if not b'Sahara protocol completed' in output:
                return output
            else:
                return 'success'

    def reboot2edl(self,adb: ADB):
        adb.adb('reboot edl')
        self.intosahara()

    def qsaharaserver(self,args):
        return run_wait(f'{self.qsspath} {args}')
    
    def fh_loader(self,args):
        return run_wait(f'{self.fhlpath} {args}')
    
    def fh_loader_err(self,args):
        output = self.fh_loader(args)
        if type(output) == str:
            if not 'All Finished Successfully' in output:
                return output
            else:
                return 'success'
        else:
            if not b'All Finished Successfully' in output:
                return output
            else:
                return 'success'
            
    def exit9008(self):
        output = self.fh_loader(rf'--port="\\.\COM{self.port}" --sendxml="ResetToEDL.xml" --search_path="bin/" --noprompt --showpercentagecomplete --zlpawarehost="1" --memoryname=""emmc""')
        if type(output) == str:
            if not 'All Finished Successfully' in output:
                return output
            else:
                return 'success'
        else:
            if not b'All Finished Successfully' in output:
                return output
            else:
                return 'success'
    
    def load_xml(self,xml_path,memory='EMMC'):
        output = self.fh_loader(rf'--port="\\.\COM{self.port}" --memoryname="{memory}" --sendxml="{xml_path}" --convertprogram2read --noprompt')
        if type(output) == str:
            if not 'All Finished Successfully' in output:
                return output
            else:
                return 'success'
        else:
            if not b'All Finished Successfully' in output:
                return output
            else:
                return 'success'
    def emmcdl(self,args):
        return run_wait(f'{self.emmcdlpath} {args}')
    
    def get_partitions_info(self):
        output = self.emmcdl(f'-p COM{self.port} -f {self.mbn} -gpt')

        partlist = []
        
        for i in output.splitlines():
            if len(i) > 0:
                if i[0].isdigit():
                    partlist.append(i)
        
        if not len(partlist) == 0:
            partitions = {}
            for i in partlist:
                split = i.split(' ')
                partitions[split[3]] = {'start': int(split[6]), 'size': int(split[10])}
            return partitions
        else:
            return output
    
    def read_partition(self,name: str,start: int = None,size = None):
        xml = '''<?xml version="1.0" ?>
<data>
  <program SECTOR_SIZE_IN_BYTES="512" file_sector_offset="0" filename="__name__.img" label="__name__" num_partition_sectors="__size__" physical_partition_number="0" size_in_KB="__size_kb__" sparse="false" start_byte_hex="__start_hex__" start_sector="__start__" />
</data>
'''
        if start is None or size is None:
            partition = self.get_partitions_info()[name]
            start = partition['start']
            size = partition['size']
        
        if os.path.exists(f'{name}.img'):
            os.remove(f'{name}.img')
        
        xml = xml.replace('__name__',name)
        xml = xml.replace('__size__',str(size),)
        xml = xml.replace('__size_kb__',str(size/2)+'.0')
        xml = xml.replace('__start_hex__','0x{:02X}'.format(int(start/8)).ljust(10,'0'))
        xml = xml.replace('__start__',str(start))

        with open(f'{name}.xml','w') as f:
            f.write(xml)
        
        output = self.load_xml(f'{name}.xml')

        os.remove(f'{name}.xml')

        return output
    def read_partitions(self,partitions: list,output: str = None):
        """
        {
            'name': {'start': start, 'size': size},
            'name': {'start': start, 'size': size},
        }
        """
        if not output is None:
            if not os.path.exists(output):
                os.mkdir(output)
        for i in partitions:
            output = self.read_partition(i)
            if not output == 'success':
                input()
                print_error(f'读取分区{i}失败',output)
            else:
                if not output is None:
                    shutil.copy(f'{i}.img',output)
    
    def write_partition(self,file: str,name: str,start: int = None,size: int = None):
        xml = '''<?xml version="1.0" ?>
<data>
  <program SECTOR_SIZE_IN_BYTES="512" file_sector_offset="0" filename="__name__.img" label="__name__" num_partition_sectors="__size__" physical_partition_number="0" size_in_KB="__size_kb__" sparse="false" start_byte_hex="__start_hex__" start_sector="__start__" />
</data>
'''
        if start is None or size is None:
            partition = self.get_partitions_info()[name]
            start = partition['start']
            size = partition['size']
        
        if not os.path.abspath(file) == os.path.abspath(f'tmp/{name}.img'):
            if os.path.exists(f'tmp/{name}.img'):
                os.remove(f'tmp/{name}.img')
            shutil.copy(file,f'tmp/{name}.img')
        
        xml = xml.replace('__name__',name)
        xml = xml.replace('__size__',str(size),)
        xml = xml.replace('__size_kb__',str(size/2)+'.0')
        xml = xml.replace('__start_hex__','0x{:02X}'.format(int(start/8)).ljust(10,'0'))
        xml = xml.replace('__start__',str(start))

        with open(f'{name}.xml','w') as f:
            f.write(xml)
        
        output = self.fh_loader_err(rf'--port=\\.\COM{self.port} --memoryname=emmc --search_path=tmp/ --sendxml={name}.xml --noprompt')

        os.remove(f'{name}.xml')
        os.remove(f'tmp/{name}.img')

        return output
    
    def write_partitions(self,partitions: list):
        """
        {
            'name': {'file': filepath, 'start': start, 'size': size},
            'name': {'file': filepath, 'start': start, 'size': size},
        }
        """
        for i in partitions:
            output = self.write_partition(partitions[i]['file'],i)
            if not output == 'success':
                print_error(f'写入分区{i}失败',output)
                input()
                break

def extract_files(zip_path,extract_files,extract_path,filetree=False):
    if type(extract_files) == str():
        extract_files = [extract_files]
    with zipfile.ZipFile(zip_path,'r') as zipf:
        for i in extract_files:
            try:
                zipf.extract(i,extract_path)
            except:
                pass
    if not filetree:
        if not extract_path[-1] == '/' or not extract_path[-1] == '\\':
            extract_path = extract_path + '/'
        for i in extract_files:
            if '/' in i or '\\' in i:
                try:
                    shutil.copy(extract_path+i,extract_path)
                    os.remove(extract_path+i)
                except:
                    pass
        for i in os.listdir(extract_path):
            try:
                os.rmdir(extract_path+i+'/')
            except:
                pass

def extract_all(zip_path,extract_path):
    with zipfile.ZipFile(zip_path,'r') as zipf:
        zipf.extractall(extract_path)

def easy_patch_boot():
    pass

class MAGISKBOOT:
    def __init__(self,path):
        self.path = path
    def magiskboot(self,args):
        output = run_wait(f'{self.path} {args}')
        return output

def patch_boot(
        magiskboot_path: str,
        input_path: str,
        magisk_path: str,
        output_path: str,
        log,
        options={
            'keep_verity':True,
            'keep_force_encrypt':True,
            'patch_vbmeta_flag':False,
            'recovery_mode':False,
            'legacy_sar':True,
            'system_root':True,
            'arch':'arm_32',
            'rootfs':False
        }
    ):
    magiskboot = MAGISKBOOT(magiskboot_path).magiskboot
    tmpfile = []

    #准备magisk
    with zipfile.ZipFile(magisk_path) as zipf:
        namelist = zipf.namelist()
        for i in ['arm/magiskinit','lib/armeabi-v7a/libmagiskinit.so']:
            if i in namelist:
                tmpfile.append('magiskinit')
                zipf.extract(i)
                shutil.copy(i,'./magiskinit')
                shutil.rmtree(i.split('/')[0]+'/')
                break
        
        if not os.path.exists('./magiskinit'):
            raise FileNotFoundError('Cannot found magiskinit in zip!')

        if 'lib/armeabi-v7a/libmagisk32.so' in namelist:
            tmpfile += ['libmagisk32.so','magisk32.xz']
            zipf.extract('lib/armeabi-v7a/libmagisk32.so')
            shutil.copy('lib/armeabi-v7a/libmagisk32.so','./')
            shutil.rmtree('lib/')
            magiskboot('compress=xz libmagisk32.so magisk32.xz')
        
        if 'assets/stub.apk' in namelist:
            tmpfile += ['stub.apk','stub.xz']
            zipf.extract('assets/stub.apk')
            shutil.copy('assets/stub.apk','./stub.apk')
            shutil.rmtree('assets/')
            magiskboot('conpress=xz stub.apk stub.xz')

        for i in ['assets/util_functions.sh','common/util_functions.sh']:
            if i in namelist:
                tmpfile.append('util_functions.sh')
                zipf.extract(i)
                shutil.copy(i,'./util_functions.sh')
                shutil.rmtree(i.split('/')[0]+'/')
                break
        if os.path.exists('util_functions.sh'):
            with open('util_functions.sh','r') as f:
                read = f.read()
                magisk_vercode = re.search('MAGISK_VER_CODE=.*',read).group().split('=')[1]
        else:
            raise FileNotFoundError('Cannot found util_functions.sh in zip!')

    #解包boot
    log('解包boot')
    magiskboot(f'unpack -h {input_path}')
    tmpfile += ['kernel','kernel_dtb','ramdisk.cpio','header']

    #测试ramdisk
    if os.path.exists('ramdisk.cpio'):
        patchmode = run_wait(f'{magiskboot_path} cpio ramdisk.cpio test',returncode=True)
    else:
        patchmode = 0
    
    if patchmode == 0:
        #模式0
        sha1 = magiskboot(f'sha1 {input_path}').replace('\n','').replace('\r','') #获取sha1
        if os.path.exists('ramdisk.cpio'):
            shutil.copy('ramdisk.cpio','ramdisk.cpio.orig') #备份ramdisk.cpio
            tmpfile.append('ramdisk.cpio.orig')
    elif patchmode == 1:
        #模式1
        sha1 = magiskboot('cpio ramdisk.cpio sha1').replace('\n','').replace('\r','') #获取sha1
        magiskboot('cpio ramdisk.cpio restore') #还原ramdisk.cpio
        shutil.copy('ramdisk.cpio','ramdisk.cpio.orig') #备份ramdisk.cpio
        tmpfile.append('ramdisk.cpio.orig')

    #修补ramdisk.cpio
        log('修补ramdisk.cpio')
    with open('config','w',newline='\n') as f:
        if magisk_vercode == '20400':
            f.write(f'''KEEPVERITY={options['keep_verity']}
KEEPFORCEENCRYPT={options['keep_force_encrypt']}
RECOVERYMODE={options['recovery_mode']}
SHA1={sha1}''')
        elif magisk_vercode == '25200' or magisk_vercode == '25210':
            f.write(f'''KEEPVERITY={options['keep_verity']}
KEEPFORCEENCRYPT={options['keep_force_encrypt']}
RECOVERYMODE={options['recovery_mode']}
PATCHVBMETAFLAG={options['patch_vbmeta_flag']}
SHA1={sha1}''')
    tmpfile.append('config')

    if magisk_vercode == '20400':
        shutil.copy('bin/711_adbd','./')
        tmpfile.append('711_adbd')
        magiskboot(r'cpio ramdisk.cpio "add 750 init magiskinit" "patch" "backup ramdisk.cpio.orig" "mkdir 000 .backup" "add 000 .backup/.magisk config" "add 0750 sbin/adbd 711_adbd"')
    elif magisk_vercode == '25200' or magisk_vercode == '25210':
        shutil.copy('bin/810_adbd','./')
        tmpfile.append('810_adbd')
        magiskboot(r'cpio ramdisk.cpio "add 0750 init magiskinit" "mkdir 0750 overlay.d" "mkdir 0750 overlay.d/sbin" "add 0644 overlay.d/sbin/magisk32.xz magisk32.xz" "patch" "backup ramdisk.cpio.orig" "mkdir 000 .backup" "add 000 .backup/.magisk config" "add 0750 sbin/adbd 810_adbd"')

    #修补dtb
    log('修补dtb')
    magiskboot('dtb kernel_dtb patch')

    #修补kernel
    log('修补kernel')
    magiskboot('hexpatch kernel 49010054011440B93FA00F71E9000054010840B93FA00F7189000054001840B91FA00F7188010054 A1020054011440B93FA00F7140020054010840B93FA00F71E0010054001840B91FA00F7181010054') #尝试修补kernel-移除三星RKP
    magiskboot('hexpatch kernel 821B8012 E2FF8F12') #尝试修补kernel-移除三星defex
    if options['rootfs']:
        magiskboot('hexpatch kernel 736B69705F696E697472616D667300 77616E745F696E697472616D667300') #尝试修补kernel-强制开启rootfs
    else:
        magiskboot('hexpatch kernel 77616E745F696E697472616D667300 736B69705F696E697472616D667300') #尝试修补kernel-关闭rootfs
    
    patch()
    
    #打包boot
    log('打包boot')
    magiskboot(f'repack {input_path} boot_new.img')
    shutil.copy('boot_new.img',output_path)
    tmpfile.append('boot_new.img')

    #清理临时文件
    for i in tmpfile:
        if os.path.exists(i):
            os.remove(i)
    

def iferror(output,title,status: rich.status.Status,*,mode='skip',qt: QT = None):
    if not output == 'success':
        status.stop()
        print_error(f'{title}失败!',output)
        if mode == 'skip':
            pass
        elif mode == 'exit9008':
            qt.exit9008()
            print('按下回车键退出')
            exit_after_enter()
        elif mode == 'stop':
            print('按下回车键退出')
            exit_after_enter()

'''
I17D=Q1S
I11=Z3
IB=Z3
I12=Z2
I13=Z5q
I13C=Z5A
I18=Z6
I17=Z1S
I16=Z1
GLI17=imoo_Z2
DI02=Q2
HKI17=Z2H
I19=Z5Pro
IDI13=imoo_Z5
THI17=imoo_Z2
PHI17=imoo_Z2
I20=Z6_DFB
I28=D3
I26A=Z5_SXB
I25=Z7
I25C=Z7A
I25D=Z7S
I32=Z8
ND01=Z9
ND07=Z8A
ND03=Z10
'''
xtc_models = {
    'I17D':'Q1S',
    'IB':'Z3',
    'I12':'Z2',
    'I13':'Z5q',
    'I13C':'Z5A',
    'I18':'Z6',
    'I16':'Z1',
    'I17':'Z1S',
    'DI02':'Q2',
    'I19':'Z5Pro',
    'I20':'Z6_DFB',
    'I28':'D3',
    'I25':'Z7',
    'I25C':'Z7A',
    'I25D':'Z7S',
    'I32':'Z8',
    'ND01':'Z9',
    'ND07':'Z8A',
    'ND03':'Z10',
    'I32-QCH':'Z8',
    'ND01-SN':'Z9',
}

def is_v3(model: str,version: str):
    versions = {
        'Z6_DFB': '2.6.5',
        'Z7': '2.3.8',
        'Z7A': '1.7.8',
        'Z7S': '1.4.6',
        'Z8': '2.8.5',
        'Z9': '3.0.2',
        'Z8A': '1.3.0'
    }
    version = int(version.replace('.',''))
    return version >= int(versions[model].replace('.',''))

class FASTBOOT:
    def __init__(self,path):
        self.path = path
    def fastboot(self,args):
        return run_wait(f'{self.path} {args}')
    def wait_for_fastboot(self):
        while True:
            if 'fastboot' in self.fastboot('devices'):
                break
            sleep(0.5)
    def flash(self,part,img):
        output = self.fastboot(f'flash {part} {img}')
        if type(output) == str:
            if not 'Finished' in output:
                return output
            else:
                return 'success'
        else:
            if not b'Finished' in output:
                return output
            else:
                return 'success'
    def erase(self,part):
        output = self.fastboot(f'erase {part}')
        if type(output) == str:
            if not 'Finished' in output:
                return output
            else:
                return 'success'
        else:
            if not b'Finished' in output:
                return output
            else:
                return 'success'
        

def install_driver():
    run_wait('bin/qualcommdriver.msi /q')
    run_wait('pnputil -a -i bin/fastbootdriver/*.inf')