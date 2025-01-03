import os
from time import sleep
import json
import tools
import subprocess
import sys
import noneprompt
import requests
from rich.console import Console
from rich.table import Table
import shutil
import threading
from tkinter import filedialog
import traceback

version = [1,8]

os.system(f'title XTCEasyRootPlus v{version[0]}.{version[1]}')
console = Console()
status = console.status('')
print = console.print

class Logging:
    def __init__(self, console: Console, logging: tools.Log.logging):
        self.logging = logging
        self.console = console
    def log(self,log):
        self.console.log(log)
        self.logging(log)

log = Logging(console, tools.logging).log

if not os.path.exists('tmp/'):
    os.mkdir('tmp')
else:
    for i in os.listdir('tmp'):
        if os.path.isfile(f'tmp/{i}'):
            os.remove(f'tmp/{i}')
        else:
            shutil.rmtree(f'tmp/{i}')

if not os.path.exists('data/'):
    os.mkdir('data')

if len(version) == 3 and version[2] == 'b':
    print('[red][!][/red]警告:这是一个测试版本,非常不稳定,若非测试人员请勿使用!')
    sleep(5)

try:
    #检查更新
    os.system('cls')
    status.update('正在检查更新')
    status.start()
    log('检查最新版本')
    try: #尝试获取版本文件
        with requests.get('https://cn-nb1.rains3.com/xtceasyrootplus/version.json') as r:   #获取版本信息
            read = json.loads(r.content)
        latest_version = read
        if latest_version[0] >= version[0] and latest_version[1] > version[1]:
            log(f'发现新版本:{latest_version[0]}.{latest_version[1]}')
            log('开始下载新版本......')
            status.stop()
            tools.download_file('https://cn-nb1.rains3.com/xtceasyrootplus/XTCEasyRootPlusInstaller.exe','tmp/XTCEasyRootPlusInstaller.exe')
            subprocess.Popen('tmp/XTCEasyRootPlusInstaller.exe')
            sys.exit()
    except requests.ConnectionError:   #捕捉下载失败错误
        log('检查更新失败，请检查你的网络或稍后再试')
        status.stop()
        tools.exit_after_enter() #退出

    log('当前版本为最新!')
    sleep(1)

    if not os.path.exists('driver'):
        log('初次使用,自动安装驱动!')
        status.update('安装驱动')
        log('安装Qualcomm驱动')
        tools.run_wait('pnputil /i /a bin/qualcommdriver/*.inf')
        log('安装Fastboot驱动')
        tools.run_wait('pnputil /i /a bin/fastbootdriver/*.inf')
        log('安装驱动完毕!')
        open('driver','w').close()
        sleep(1)

    while True:
        #清屏并停止状态指示
        status.stop()
        os.system('cls')

        adb = tools.ADB('bin/adb.exe')

        #主菜单
        tools.print_logo(version)
        print(f'\nXTCEasyRootPlus [blue]v{version[0]}.{version[1]}[/blue]')
        print('本软件是[green]免费公开使用[/green]的，如果你是付费买来的请马上退款，你被骗了！\n')

        match noneprompt.ListPrompt(
            '请选择功能',
            [
                noneprompt.Choice('1.一键Root'),
                noneprompt.Choice('2.超级恢复(救砖/降级/恢复原版系统)'),
                noneprompt.Choice('3.工具箱'),
                noneprompt.Choice('4.关于')
            ]
        ).prompt().name:


            case '1.一键Root':
                console.rule('免责声明',characters='=')
                print('''1.所有已经解除第三方软件安装限制的手表都可以恢复到解除限制前之状态。
2.解除第三方软件安装限制后，您的手表可以无限制地安装第三方软件，需要家长加强对孩子的监管力度，避免孩子沉迷网络，影响学习；手表自带的功能不受影响。
3.您对手表进行解除第三方软件安装限制之操作属于您的自愿行为，若在操作过程中由于操作不当等自身原因，导致出现手表无法正常使用等异常情况，以及解除软件安装限制之后产生的一切后果将由您本人承担！''')
                console.rule('免责声明',characters='=')
                confirm = noneprompt.ConfirmPrompt('你是否已阅读并同意本《免责声明》',default_choice=False).prompt()
                if not confirm:
                    continue
                input('请拔出手表上的SIM卡,拔出后按下回车下一步')
                print('\r',end='')
                status.update("等待设备连接")
                status.start()
                print('请在手表上打开并用数据线将手表连接至电脑')
                adb.wait_for_connect()

                log('设备已连接')
                status.update('获取设备信息')
                log('获取设备信息')
                info = adb.get_info()
                sdk_version = adb.get_version_of_sdk()
                model = tools.xtc_models[info['innermodel']]
                android_version = info['version_of_android_from_sdk']
                table = Table()
                table.add_column("型号", width=12)
                table.add_column("代号")
                table.add_column("系统版本", justify="right")
                table.add_column("安卓版本", justify="right")
                table.add_row(model,info['innermodel'],info['version_of_system'],android_version)
                print(table)
                status.stop()
                if not info['innermodel'] in tools.xtc_models.keys():
                    print('你的设备貌似不是小天才设备,或者还没被支持,目前暂不支持一键Root')
                    print('按下回车键退出')
                    tools.exit_after_enter()
                elif tools.xtc_models[info['innermodel']] == 'Z10':
                    print('Z10不支持Root!')
                    print('按下回车退出')
                    tools.exit_after_enter()

                if android_version == '8.1':
                    choice = noneprompt.ListPrompt(
                        '请选择想要的Magisk版本',
                        choices=[
                            noneprompt.Choice('1.Magisk25200'),
                            noneprompt.Choice('2.MagiskDelta25210')
                        ],
                    ).prompt()
                    if choice.name == '1.Magisk25200':
                        magisk = '25200'
                    elif choice.name == '2.MagiskDelta25210':
                        magisk = '25210'

                if not os.path.exists(f'data/{model}'):
                    log('下载文件')
                    status.update('下载文件')
                    tools.download_file(f'https://cn-nb1.rains3.com/xtceasyrootplus/{model}.zip',f'tmp/{model}.zip')

                    log('解压文件')
                    status.update('解压文件')
                    tools.extract_all(f'tmp/{model}.zip',f'data/{model}/')

                if android_version == '8.1':
                    if magisk == '25200':
                        tools.download_file('https://cn-nb1.rains3.com/xtceasyrootplus/1userdata.img','tmp/userdata.img')
                    elif magisk == '25210':
                        tools.download_file('https://cn-nb1.rains3.com/xtceasyrootplus/2userdata.img','tmp/userdata.img')

                with requests.get('https://cn-nb1.rains3.com/xtceasyrootplus/launchers.json') as r:
                    if android_version == '7.1':
                        launchers: dict = json.loads(r.content)['711']
                    elif android_version == '8.1':
                        launchers: dict = json.loads(r.content)['810']
                    if not len(launchers) == 1:
                        choices = []
                        for i in list(launchers.keys()):
                            choices.append(noneprompt.Choice(i))
                        choice = noneprompt.ListPrompt('请选择桌面版本(若不知道怎么选择直接选第一项即可)',choices,default_select=1).prompt().name
                        launcher = launchers[choice]
                    else:
                        launcher = list(launchers.values())[0]

                status.stop()

                def download_all_files():
                    if android_version == '7.1':
                        filelist = ['appstore.apk','moyeinstaller.apk','xtctoolbox.apk','filemanager.apk','notice.apk','toolkit.apk',launcher,'xws.apk','wxzf.apk']
                        for i in filelist:
                            tools.download_file(f'https://cn-nb1.rains3.com/xtceasyrootplus/apps/{i}',f'tmp/{i}',progress=False)
                    elif android_version == '8.1':
                        filelist = ['appstore.apk','notice.apk','wxzf.apk','wcp2.apk','datacenter.apk','xws.apk',launcher,'11605.apk','filemanager.apk','settings.apk']
                        for i in filelist:
                            tools.download_file(f'https://cn-nb1.rains3.com/xtceasyrootplus/apps/{i}',f'tmp/{i}',progress=False)
                        tools.download_file(f'https://cn-nb1.rains3.com/xtceasyrootplus/xtcpatch/{model}.zip','tmp/xtcpatch.zip',progress=False)

                download_thread = threading.Thread(target=download_all_files)
                download_thread.start()

                if android_version == '7.1':
                    choice = noneprompt.ListPrompt(
                        '请选择Root方案',
                        choices=[
                            noneprompt.Choice('1.boot方案(如果你已经降级选这个)'),
                            noneprompt.Choice('2.recovery方案(如果你没有用过超级恢复/降级选这个)')
                        ]
                        ).prompt()
                    if choice.name == '1.boot方案(如果你已经降级选这个)':
                        mode = 'boot'
                    elif choice.name == '2.recovery方案(如果你没有用过超级恢复/降级选这个)':
                        mode = 'recovery'


                while True:
                    confirm = noneprompt.ConfirmPrompt('你是否已经将SIM卡拔出?',default_choice=False).prompt()
                    if confirm:
                        break
                    else:
                        print('请将SIM卡拔出!')
                while True:
                    confirm = noneprompt.ConfirmPrompt('请确认你已经将SIM卡拔出!否则若Root后出现「手表验证异常」我们概不负责!',default_choice=False).prompt()
                    if confirm:
                        break
                    else:
                        print('请将SIM卡拔出!')

                output = adb.shell('getprop gsm.xtcplmn.plmnstatus')
                if '没有服务' in output:
                    status.stop()
                    input('手表状态:无服务,请确定您已拔卡!如果不想喜提「手表验证异常」请先拔卡,如已拔卡无视此提示')
                elif '只能拨打紧急电话' in output:
                    status.stop()
                    input('您似乎没有拔卡!如果不想喜提「手表验证异常」请先拔卡,如已拔卡无视此提示')

                if android_version == '7.1':
                    status.update('重启设备至9008模式')
                    status.start()
                    log('重启设备至9008模式')
                    adb.adb('reboot edl')
                    log('等待连接')
                    port = tools.wait_for_edl()

                    log('连接成功,开始读取boot分区')
                    status.update('读取boot分区')
                    qt = tools.QT('bin/QSaharaServer.exe','bin/fh_loader.exe',port,f'data/{model}/mbn.mbn')
                    tools.iferror(qt.intosahara(),'进入sahara模式',status,mode='skip')
                    tools.iferror(qt.read_partition('boot'),'读取boot分区',status,mode='exit9008',qt=qt)

                    log('读取boot分区成功!')
                    shutil.copy('boot.img','tmp/')
                    os.remove('boot.img')

                    log('开始修补boot分区')
                    status.update('修补boot分区')
                    tools.patch_boot('bin/magiskboot.exe','tmp/boot.img','bin/20400.zip','tmp/',log)
                    log('修补完毕')

                    if mode == 'boot':
                        log('重新刷入boot')
                        status.update('刷入boot')
                        tools.iferror(qt.write_partition('tmp/boot_new.img','boot'),'刷入boot分区',status,mode='exit9008',qt=qt)

                    elif mode == 'recovery':
                        log('刷入recovery')
                        status.update('刷入recovery')
                        tools.iferror(qt.write_partition('tmp/boot_new.img','recovery'),'刷入recovery',status,mode='exit9008',qt=qt)

                        log('刷入misc')
                        status.update('刷入misc')
                        tools.iferror(qt.write_partition(f'data/{model}/misc.mbn','misc'),'刷入misc',status,mode='exit9008',qt=qt)

                    log('刷入成功,退出9008模式')
                    status.update('退出9008')
                    tools.iferror(qt.exit9008(),'退出9008模式',status,mode='stop')

                    log('等待重新连接')
                    status.update('等待重新连接')
                    adb.wait_for_connect()
                    adb.wait_for_complete()

                    log('安装Magisk管理器')
                    status.update('安装Magisk管理器')
                    tools.iferror(adb.install(f'data/{model}/manager.apk'),'安装Magisk管理器',status,mode='stop')

                    log('启动管理器')
                    status.update('启动管理器')
                    sleep(5)
                    adb.shell('am start com.topjohnwu.magisk/a.c')
                    adb.push(f'data/{model}/xtcpatch','/sdcard/')
                    adb.push(f'data/{model}/magiskfile','/sdcard/')
                    adb.push('bin/2100.sh','/sdcard/')
                    log('刷入模块')
                    status.update('刷入模块')
                    adb.shell('su -c sh /sdcard/2100.sh')
                    adb.install_module('bin/xtcpatch2100.zip')
                    adb.shell('rm -rf /sdcard/xtcpatch /sdcard/magiskfile /sdcard/2100.sh')

                    if download_thread.is_alive():
                        log('下载文件')
                        status.update('下载文件')
                        download_thread.join()

                    log('安装弦-安装器')
                    adb.install('tmp/moyeinstaller.apk')

                    log('设置充电可用')
                    status.update('设置充电可用')
                    adb.shell('setprop persist.sys.charge.usable true')

                    log('模拟未充电')
                    status.update('模拟未充电')
                    adb.shell('dumpsys battery unplug')

                    status.stop()
                    console.rule('接下来需要你对手表进行一些手动操作',characters='=')
                    print('请完成激活向导,当提示绑定时直接右滑退出,完成开机向导,进入主界面')
                    input('如果你已经进入主界面,请按回车继续')
                    console.rule('',characters='=')

                    status.update('设置默认软件包管理器')
                    status.start()
                    log('设置默认软件包管理器')
                    adb.push('tmp/notice.apk','/sdcard/notice.apk')
                    if not adb.is_screen_alive():
                        adb.shell('input keyevent 26')
                    adb.shell('am start -a android.intent.action.VIEW -d file:///sdcard/notice.apk -t application/vnd.android.package-archive')

                    status.stop()
                    console.rule('接下来需要你对手表进行一些手动操作',characters='=')
                    print('现在你的手表上出现了一个白色的"打开方式"对话框,请往下滑选择"使用弦安装器"并点击始终按钮;点击始终按钮后会弹出安装notice的对话框,点击取消即可')
                    input('如果你已经进入主界面,请按回车继续')
                    console.rule('',characters='=')
                    status.start()

                    log('安装Xposed Manager')
                    status.update('安装Xposed Manager')
                    tools.iferror(adb.install('bin/xposed-magisk.apk',[]),'安装Xposed Manager',status,mode='stop')

                    if mode == 'recovery':
                        log('重启设备至9008模式')
                        status.update('等待连接')
                        adb.adb('reboot edl')
                        port = tools.wait_for_edl()

                        log('进入sahara模式')
                        status.update('进入sahara模式')
                        tools.iferror(qt.intosahara(),'进入sahara模式',status,mode='stop')

                        log('刷入recovery')
                        status.update('刷入recovery')
                        tools.iferror(qt.write_partition('tmp/boot_new.img','recovery'),'刷入recovery',status,mode='exit9008',qt=qt)

                        log('刷入misc')
                        status.update('刷入misc')
                        tools.iferror(qt.write_partition(f'data/{model}/misc.mbn','misc'),'刷入misc',status,mode='exit9008',qt=qt)

                        log('退出9008模式')
                        status.update('等待重新连接')
                        tools.iferror(qt.exit9008(),'退出9008模式',status,mode='stop')

                        adb.wait_for_connect()
                        adb.wait_for_complete()

                    log('安装Xposed-[white]1[/white]')
                    status.update('安装Xposed')
                    adb.install_module('bin/xposed-magisk-1.zip')
                    log('重启设备')
                    log('提示:首次刷入Xposed后开机可能需要[bold]7-15分钟[/bold],请耐心等待')
                    status.update('等待重新连接')
                    adb.adb('reboot')
                    adb.wait_for_connect()
                    adb.wait_for_complete()
                    log('连接成功')

                    log('安装Xposed-[white]2[/white]')
                    status.update('安装Xposed')
                    adb.install_module('bin/xposed-magisk-2.zip')
                    log('重启设备')
                    status.update('等待重新连接')
                    adb.adb('reboot')
                    adb.wait_for_connect()
                    adb.wait_for_complete()
                    log('连接成功')

                    status.update('安装核心破解')
                    log('安装核心破解')
                    tools.iferror(adb.install('tmp/toolkit.apk'),'安装核心破解',status,mode='stop')

                    status.update('设置充电可用')
                    log('设置充电可用')
                    adb.shell('setprop persist.sys.charge.usable true')

                    log('充电可用已开启')
                    log('模拟未充电状态')
                    status.update('模拟未充电状态')
                    adb.shell('dumpsys battery unplug')
                    log('已模拟未充电状态')
                    status.stop()

                    console.rule('接下来需要你对手表进行一些手动操作',characters='=')
                    input('请打开手表上的"Xposed Installer"应用,点击左上角的三条杠,点击"模块",勾选"核心破解"选项\n完成操作后请按回车继续')
                    console.rule(characters='=')

                    status.update('等待重新连接')
                    status.start()
                    log('重启手表')
                    adb.adb('reboot')
                    adb.wait_for_connect()
                    adb.wait_for_complete()

                    log('连接成功!')
                    status.update('安装改版桌面')
                    log('开始安装改版系统桌面')
                    tools.iferror(adb.install(f'tmp/{launcher}'),f'安装{launcher}',status,mode='stop')

                    status.update('等待重新连接')
                    log('重启手表')
                    adb.adb('reboot')
                    adb.wait_for_connect()
                    adb.wait_for_complete()

                    log('安装必备软件')
                    status.update('安装必备软件')
                    for i in os.listdir(f'tmp/'):
                        if i[-3:] == 'apk' and not i == 'moyeinstaller.apk' and not i == launcher and not i == 'toolkit.apk':
                            log(f'安装{i}')
                            tools.iferror(adb.install(f'tmp/{i}'),f'安装{i}',status,mode='skip')

                    status.stop()
                    # log('恭喜你,你的手表ROOT完毕!')
                    input('恭喜你,Root成功!按回车返回主界面')




                elif android_version == '8.1':
                    is_v3 = tools.is_v3(model,info['version_of_system'])
                    status.update('等待连接') 
                    status.start()
                    log('重启设备至9008模式')
                    adb.adb('reboot edl')
                    log('等待连接')
                    port = tools.wait_for_edl()

                    log('连接成功')
                    log('开始读取boot分区')
                    status.update('读取boot分区') 
                    qt = tools.QT('bin/QSaharaServer.exe','bin/fh_loader.exe',port,'bin/msm8937.mbn')
                    tools.iferror(qt.intosahara(),'进入sahara模式',status,mode='stop')
                    tools.iferror(qt.read_partition('boot'),'读取boot分区',status,mode='exit9008',qt=qt)

                    log('读取boot分区成功!')
                    shutil.copy('boot.img','tmp/')
                    os.remove('boot.img')

                    log('开始修补boot分区')
                    status.update('修补boot分区') 
                    tools.patch_boot('bin/magiskboot.exe','tmp/boot.img',f'bin/{magisk}.apk','tmp/',log)

                    log('修补完毕')
                    if model in ('Z7A','Z6_DFB'):
                        log('刷入recovery')
                        status.update('刷入recovery') 
                        tools.iferror(qt.write_partition('tmp/boot_new.img','recovery'),'刷入recovery',status,mode='exit9008',qt=qt)
                    elif not is_v3:
                        log('刷入boot')
                        status.update('刷入boot') 
                        tools.iferror(qt.write_partition('tmp/boot_new.img','boot'),'刷入boot',status,mode='exit9008',qt=qt)
                    log('刷入aboot,recovery')
                    status.update('刷入aboot,recovery')
                    tools.iferror(qt.fh_loader_err(rf'--port=\\.\COM{port} --memoryname=emmc --search_path=data/{model}/ --sendxml=data/{model}/rawprogram0.xml --noprompt'),'刷入rawprogram',status,mode='stop')
                    log('刷入成功!')
                    if not model in ('Z7A','Z6_DFB') and is_v3:
                        status.update('刷入空boot'), 
                        log('刷入空boot')
                        tools.iferror(qt.write_partition('bin/eboot.img','boot'),'刷入空boot',status,mode='exit9008',qt=qt)
                    tools.iferror(qt.exit9008(),'退出9008模式',status,mode='stop')
                    status.update('退出9008')
                    log('退出9008模式')
                    status.update('等待重新连接') 
                    fastboot = tools.FASTBOOT('bin/fastboot.exe')
                    if not model in ('Z7A','Z6_DFB'):
                        if is_v3:
                            fastboot.wait_for_fastboot()
                            status.update('刷入boot') 
                            log('刷入boot')
                            tools.iferror(fastboot.flash('boot','tmp/boot_new.img'),'刷入boot',status,mode='stop')
                        else:
                            adb.wait_for_connect()
                            adb.wait_for_complete()
                            adb.adb('reboot bootloader')
                            fastboot.wait_for_fastboot()
                        status.update('刷入userdata') 
                        log('刷入userdata')
                        tools.iferror(fastboot.flash('userdata','tmp/userdata.img'),'刷入userdata',status)
                        status.update('刷入misc') 
                        log('刷入misc')
                        with open('tmp/misc.bin','w') as f:
                            f.write('ffbm-02')
                        tools.iferror(fastboot.flash('misc','tmp/misc.bin'),'刷入misc',status)
                        fastboot.fastboot('reboot')
                        status.update('等待重新连接') 
                        log('刷入完毕,重启进入系统')
                    adb.wait_for_connect()
                    adb.wait_for_complete()
                    log('连接成功')
                    if is_v3:
                        log('创建空文件')
                        status.update('创建空文件')
                        adb.shell('mkdir /data/adb/modules/XTCPatch/system/app/XTCLauncher')
                        adb.shell('touch /data/adb/modules/XTCPatch/system/app/XTCLauncher/XTCLauncher.apk')
                        log('重启设备')
                        status.update('等待重新连接')
                        adb.adb('reboot')
                        adb.wait_for_connect()
                        adb.wait_for_complete()
                        log('连接成功!')
                        if download_thread.is_alive():
                            log('下载文件')
                            status.update('下载文件')
                            download_thread.join()
                        log('安装11605桌面')
                        status.update('安装桌面')
                        tools.iferror(adb.install('bin/11605launcher.apk'),'安装11605桌面',status,mode='stop')
                        log('重启设备')
                        status.update('等待连接')
                        adb.adb('reboot')
                        adb.wait_for_connect()
                        adb.wait_for_complete()

                    if not model in ('Z7A','Z6_DFB'):
                        status.update('等待连接') 
                        log('重启进入Fastboot')
                        adb.adb('reboot bootloader')
                        fastboot.wait_for_fastboot()
                        status.update('擦除misc') 
                        log('擦除misc')
                        fastboot.erase('misc')
                        status.update('等待重新连接') 
                        log('刷入完毕,重启进入系统')
                        log('提示:若已进入系统但仍然卡在这里,请打开拨号盘输入"*#0769651#*"手动开启adb')
                        fastboot.fastboot('reboot')
                        adb.wait_for_connect()
                        adb.wait_for_complete()

                    # choice = noneprompt.ListPrompt('现在您的手表处于什么状态?',choices=[noneprompt.Choice('1.已正常开机'),noneprompt.Choice('2.仍处于黑屏状态')]).prompt()
                    # if choice.name == '2.仍处于黑屏状态':
                    #     pass
                    log('开启充电可用')
                    status.update('开启充电可用')
                    adb.shell('setprop persist.sys.charge.usable true')
                    log('模拟未充电')
                    status.update('模拟未充电')
                    adb.shell('dumpsys battery unplug')
                    status.stop()

                    console.rule('接下来需要你进行一些手动操作',characters='=')
                    print('请完成激活向导,当提示绑定时直接右滑退出,完成开机向导,进入主界面')
                    print('提示:请不要断开手表与电脑的连接!')
                    print('提示:如果提示系统已被Root不用在意,没事的,点击我知道了就行')
                    input('如果你已经进入主界面,请按回车进行下一步')
                    console.rule('',characters='=')

                    status.update('设置DPI')
                    status.start()
                    log('设置DPI为200')
                    adb.shell('wm density 200')
                    log('检测桌面是否崩溃')
                    status.update('检测桌面是否崩溃')
                    sleep(5)
                    if not 'com.xtc.i3launcher' in adb.get_activity():
                        log('检测到桌面崩溃!设置DPI为280')
                        status.update('设置DPI')
                        adb.shell('wm density 280')
                        log('请点击屏幕上的"重新打开应用"')
                        status.update('等待点击')
                        while True:
                            if 'com.xtc.i3launcher' in adb.get_activity():
                                break
                            sleep(0.5)

                    status.stop()
                    console.rule('接下来需要你进行一些手动操作',characters='=')
                    input('请打开手表上的"Magisk"或"MagiskDelta"APP,点击右上角设置,往下滑找到自动响应,将其设置为"允许";然后找到"超级用户通知",将其设置为"无",完成后按下回车继续')
                    input('请打开手表上的"Edxposed Installer"APP,然后直接返回退出,完成后按下回车继续')
                    input('请打开手表上的"SystemPlus"APP,滑到最下面点击"自激活",依次点击"激活SystemPlus"和"激活核心破解"按钮,完成后按下回车继续')
                    console.rule('',characters='=')

                    adb.push('bin/systemplus.sh','/sdcard/')
                    while True:
                        status.update('检查SystemPlus状态')
                        status.start()
                        log('检查SystemPlus状态')
                        output = adb.shell('sh /sdcard/systemplus.sh')
                        if not '1' in output:
                            break
                        else:
                            status.stop()
                            input('SystemPlus未激活!请重新按照上文提示激活!完成后按下回车继续')
                    adb.shell('rm -rf /sdcard/systemplus.sh')
                    log('SystemPlus激活成功!')

                    adb.push('bin/toolkit.sh','/sdcard/')
                    while True:
                        status.update('检查核心破解状态')
                        status.start()
                        log('检查核心破解状态')
                        output = adb.shell('sh /sdcard/toolkit.sh')
                        if not '1' in output:
                            break
                        else:
                            status.stop()
                            input('核心破解未激活!请重新按照上文提示激活!完成后按下回车继续')
                    adb.shell('rm -rf /sdcard/toolkit.sh')
                    log('核心破解激活成功!')

                    log('重启设备')
                    status.update('等待重新连接')
                    adb.adb('reboot')
                    adb.wait_for_connect()
                    adb.wait_for_complete()

                    log('获取uid')
                    status.update('获取uid')
                    chown = adb.shell('"dumpsys package com.solohsu.android.edxp.manager | grep userId="').replace('\n','').replace('\r','').split('=')[1][-5:]
                    log('更改文件所有者')
                    status.update('更改文件所有者')
                    adb.shell(f'"su -c chown {chown} /data/user_de/0/com.solohsu.android.edxp.manager/conf/enabled_modules.list"')
                    adb.shell(f'"su -c chown {chown} /data/user_de/0/com.solohsu.android.edxp.manager/conf/modules.list"')

                    if download_thread.is_alive():
                        log('下载文件')
                        status.update('下载文件')
                        download_thread.join()

                    log('安装XTCPatch')
                    status.update('安装XTCPatch')
                    adb.install_module_new('tmp/xtcpatch.zip')

                    log('安装修改版桌面')
                    status.update('安装修改版桌面')
                    tools.iferror(adb.install(f'tmp/{launcher}'),'安装修改版桌面',status,mode='stop')

                    log('重启设备')
                    status.update('等待连接')
                    if adb.is_connect():
                        adb.adb('reboot')
                    adb.wait_for_connect()
                    adb.wait_for_complete()

                    log('安装软件')
                    status.update('安装软件')
                    for i in ['notice.apk','wxzf.apk','appstore.apk','wcp2.apk','datacenter.apk','xws.apk','filemanager.apk','settings.apk']:
                        log(f'安装{i}')
                        tools.iferror(adb.install(f'tmp/{i}'),f'安装{i}',status)

                    log('设置DPI为320')
                    status.update('设置DPI')
                    adb.shell('wm density 320')

                    log('连接成功!')
                    status.stop()
                    input('恭喜你,Root成功!按回车返回主界面')

            case '2.超级恢复(救砖/降级/恢复原版系统)':
                status.update('获取超级恢复列表')
                status.start()
                log('获取超级恢复列表')
                with requests.get('https://cn-nb1.rains3.com/xtceasyrootplus/superrecovery.json') as r:
                    superrecovery : dict = json.loads(r.content)

                log('获取成功!')

                log('尝试自动识别机型')
                status.update('获取机型')
                if adb.is_connect():
                    info = adb.get_info()
                    model = tools.xtc_models[info['innermodel']]
                    log('获取成功')
                    status.stop()
                else:
                    log('获取失败,进入手动选择')
                    status.stop()
                    choice_list = []
                    for i,x in enumerate(superrecovery.keys()):
                        choice_list.append(noneprompt.Choice(f'{i+1}.{x}'))
                    choice = noneprompt.ListPrompt('请选择你的机型',choice_list).prompt()
                    model = choice.name.split('.')[-1]

                if not len(superrecovery[model]) == 1:
                    choice_list = []
                    for i in superrecovery[model].keys():
                        choice_list.append(noneprompt.Choice(i))
                    status.stop()
                    choice = noneprompt.ListPrompt('请选择超级恢复版本',choice_list).prompt()
                    status.start()
                    sr_version = choice.name
                else:
                    sr_version = list(superrecovery[model].keys())[0]

                if not os.path.exists(f'data/superrecovery/{model}_{sr_version}/'):
                    status.stop()
                    log('下载文件')
                    tools.download_file(superrecovery[model][sr_version],'tmp/superrecovery.zip')
                    log('解压文件')
                    status.update('解压文件')
                    status.start()
                    if not os.path.exists('data/superrecovery/'):
                        os.mkdir('data/superrecovery/')
                    os.mkdir(f'data/superrecovery/{model}_{sr_version}/')
                    tools.extract_all('tmp/superrecovery.zip',f'data/superrecovery/{model}_{sr_version}/')

                if model in ('Z1S','Z1y','Z2','Z3','Z5A','Z5Pro'):
                    fh_loader = 'fh_loader.exe'
                elif model == 'Z6' or model == 'Z5q':
                    if sr_version == '1.4.6' or sr_version == '3.5.1':
                        fh_loader = 'fh_loader.exe'
                    else:
                        fh_loader = 'xtcfh_loader.exe'
                else:
                    fh_loader = 'xtcfh_loader.exe'

                sendxml = ''
                sendxml_list = []
                mbn = ''
                for i in os.listdir(f'data/superrecovery/{model}_{sr_version}/'):
                    if i[:5] == 'patch' and i[-3:] == 'xml':
                        sendxml_list.append(i)
                    elif i[:10] == 'rawprogram' and i[-3:] == 'xml':
                        sendxml_list.append(i)
                    if i[:4] == 'prog' and i[-3:] == 'mbn':
                        mbn = f'data/superrecovery/{model}_{sr_version}/{i}'

                for i in sendxml_list:
                    sendxml = sendxml + i + ','
                sendxml = sendxml[:-1]

                status.update('等待连接')
                status.start()
                log('等待连接')
                while True:
                    if adb.is_connect():
                        adb.adb('reboot edl')
                        break
                    if not tools.check_edl() is False:
                        break
                port = tools.wait_for_edl()
                log('连接成功!')

                qt = tools.QT('bin/QSaharaServer.exe',f'bin/{fh_loader}',port,mbn)

                log('进入sahara模式')
                status.update('进入sahara模式')
                if not qt.intosahara() == 'success':
                    log('进入sahara模式失败,可能已经进入!尝试直接超恢')

                log('开始超恢')
                log('提示: 此过程耗时较长,请耐心等待')
                status.update('超级恢复中')
                tools.iferror(qt.fh_loader_err(rf'--port="\\.\COM{port}" --sendxml={sendxml} --search_path="data/superrecovery/{model}_{sr_version}" --noprompt --showpercentagecomplete --zlpawarehost="1" --memoryname=""emmc""'),'超级恢复',status,mode='stop')
                sleep(0.5)
                tools.iferror(qt.fh_loader_err(rf'--port="\\.\COM{port}" --setactivepartition="0" --noprompt --showpercentagecomplete --zlpawarehost="1" --memoryname=""emmc""'),'超级回复',status)
                sleep(0.5)
                tools.iferror(qt.fh_loader_err(rf'--port="\\.\COM{port}" --reset --noprompt --showpercentagecomplete --zlpawarehost="1" --memoryname=""emmc""'),'超级恢复',status)
                sleep(0.5)
                qt.exit9008()
                status.stop()
                log('超恢成功!')
                log('提示:若未开机可直接长按电源键开机进入系统')
                input('超恢成功!按下回车键回到主界面')

            case '3.工具箱':
                while True:
                    os.system('cls')
                    tools.print_logo(version)
                    print(f'\nXTCEasyRootPlus [blue]v{version[0]}.{version[1]}[/blue]\n')

                    match noneprompt.ListPrompt(
                        '请选择功能',
                        [
                            noneprompt.Choice('q.退出'),
                            noneprompt.Choice('1.安装本地应用安装包(APK)'),
                            noneprompt.Choice('2.安装模块'),
                            noneprompt.Choice('3.安装XTCPatch'),
                            noneprompt.Choice('4.安装CaremeOS Pro'),
                            noneprompt.Choice('5.模拟未充电'),
                            noneprompt.Choice('6.刷入自定义固件'),
                            noneprompt.Choice('7.分区管理器'),
                            noneprompt.Choice('8.进入qmmi模式'),
                            noneprompt.Choice('9.设置微信QQ开机自启动'),
                            noneprompt.Choice('10.启动投屏'),
                        ],
                        default_select=2
                    ).prompt().name:

                        case 'q.退出':
                            break

                        case '1.安装本地应用安装包(APK)':
                            apk = filedialog.askopenfilenames(title='请选择安装包',filetypes=[('安卓应用程序安装包','*.apk')])
                            if not adb.is_connect():
                                status.update('等待连接')
                                log('等待连接')
                                status.start()
                                adb.wait_for_connect()
                                adb.wait_for_complete()
                            status.update('开始安装')
                            status.start()
                            log('开始安装')
                            for i in apk:
                                log(f'安装{i.split('/')[-1]}')
                                output = adb.install(i)
                                if output == 'success':
                                    log('安装成功!')
                                else:
                                    status.stop()
                                    tools.print_error(f'安装{i.split('/')[-1]}失败',output)
                                    input()
                                    status.start()
                            status.stop()
                            input('安装完毕!按回车返回主界面')

                        case '2.安装模块':
                            modules = filedialog.askopenfilenames(title='请选择模块',filetypes=[('模块','*.zip')])
                            if not adb.is_connect():
                                status.update('等待连接')
                                log('等待连接')
                                status.start()
                                adb.wait_for_connect()
                                adb.wait_for_complete()
                            status.update('开始安装')
                            status.start()
                            log('开始安装')
                            android_version = adb.get_version_of_android_from_sdk()
                            for i in modules:
                                log(f'安装{i.split('/')[-1]}')
                                if android_version == '7.1':
                                    adb.install_module(i)
                                else:
                                    adb.install_module_new(i)
                            status.stop()
                            input('安装完毕!按回车返回主界面')

                        case '3.安装XTCPatch':
                            if not adb.is_connect():
                                status.update('等待连接')
                                log('等待连接')
                                status.start()
                                adb.wait_for_connect()
                                adb.wait_for_complete()
                            status.update('获取安卓版本')
                            status.start()
                            log('获取安卓版本')
                            android_version = adb.get_version_of_android_from_sdk()

                            if adb.is_xtc():
                                if android_version == '7.1':
                                    status.update('开始安装')
                                    status.start()
                                    log('开始安装')
                                    output = adb.install_module('bin/xtcpatch2100.zip')
                                    if output == 'success':
                                        log('安装成功!')
                                    else:
                                        tools.print_error('安装XTCPatch失败',output)
                                        input()
                                elif android_version == '8.1':
                                    status.update('下载文件')
                                    log('开始下载文件')
                                    model = tools.xtc_models[adb.get_innermodel()]
                                    status.stop()
                                    tools.download_file(f'https://cn-nb1.rains3.com/xtceasyrootplus/xtcpatch/{model}.zip','tmp/xtcpatch.zip')
                                    status.update('开始安装')
                                    status.start()
                                    log('开始安装')
                                    adb.push('tmp/xtcpatch.zip','/sdcard/xtcpatch.zip')
                                    adb.shell('su -c magisk --install-module /sdcard/xtcpatch.zip')
                                    adb.shell('rm -rf /sdcard/xtcpatch.zip')
                                    log('安装成功!')
                                status.stop()
                                input('安装完毕!按回车回到工具箱界面')
                            else:
                                status.stop()
                                input('你貌似不是小天才设备!按回车回到工具箱界面')

                        case '4.安装CaremeOS Pro':
                            if not adb.is_connect():
                                status.update('等待连接')
                                log('等待连接')
                                status.start()
                                adb.wait_for_connect()
                                adb.wait_for_complete()
                            status.update('获取安卓版本')
                            status.start()
                            log('获取安卓版本')
                            android_version = adb.get_version_of_android_from_sdk()

                            if adb.is_xtc():
                                if android_version == '8.1':
                                    log('开始下载文件')
                                    status.stop()
                                    tools.download_file('https://cn-nb1.rains3.com/xtceasyrootplus/caremeospro.zip','tmp/caremeospro.zip')
                                    log('开始安装')
                                    log('提示:安装CaremeOSPro可能需要耗费较长的时间,请耐心等待')
                                    status.update('安装CaremeOSPro')
                                    status.start()
                                    adb.push('tmp/caremeospro.zip','/sdcard/caremeospro.zip')
                                    adb.shell('su -c magisk --install-module /sdcard/caremeospro.zip')
                                    adb.shell('rm -rf /sdcard/caremeospro.zip')
                                    log('安装成功!')
                                    status.stop()
                                    input('安装完毕!按回车回到工具箱界面')
                                else:
                                    status.stop()
                                    input('你的机型不支持CaremeOSPro!按回车回到工具箱界面')
                            else:
                                status.stop()
                                input('你貌似不是小天才设备!按回车回到工具箱界面')

                        case '5.模拟未充电':
                            if not adb.is_connect():
                                status.update('等待连接')
                                log('等待连接')
                                status.start()
                                adb.wait_for_connect()
                                adb.wait_for_complete()
                            output = adb.shell('dumpsys battery unplug')
                            log('开启成功!')
                            input('按回车回到工具箱界面')

                        case '6.刷入自定义固件':
                            input('本功能为高级功能,若因使用不当造成的变砖我们概不负责!')
                            log('选择mbn文件')
                            mbn = filedialog.askopenfilename(title='请选择mbn文件',filetypes=[('mbn文件','*.mbn')])
                            log('选择Rawprogram文件与Patch文件')
                            sendxml_list = filedialog.askopenfilenames(title='请选择Rawprogram文件与Patch文件',filetypes=[('XML文件','rawprogram*.xml;patch*.xml')])
                            search_path = os.path.abspath(os.path.dirname(sendxml_list[0]))
                            fh_loader = {True: 'xtcfh_loader.exe',False: 'fh_loader.exe'}[noneprompt.ConfirmPrompt('是否使用小天才加密fh_loader?',default_choice=False).prompt()]

                            sendxml = ''
                            for i in sendxml_list:
                                sendxml = sendxml + i.split('/')[-1] + ','
                            sendxml = sendxml[:-1]

                            status.update('等待连接')
                            status.start()
                            log('等待连接')
                            while True:
                                if adb.is_connect():
                                    adb.adb('reboot edl')
                                    break
                                if tools.check_edl():
                                    break
                            port = tools.wait_for_edl()
                            log('连接成功!')

                            qt = tools.QT('bin/QSaharaServer.exe',f'bin/{fh_loader}',port,mbn)

                            status.update('刷入固件')
                            status.start()
                            log('开始刷入固件')
                            log('提示:此过程可能耗时较长,请耐心等待')

                            tools.iferror(qt.intosahara(),'进入sahara模式',status,mode='stop')

                            tools.iferror(qt.fh_loader_err(rf'bin/{fh_loader} --port="\\.\COM{port}" --sendxml={sendxml} --search_path="{search_path}" --noprompt --showpercentagecomplete --zlpawarehost="1" --memoryname=""emmc""'),'超级恢复',status,mode='stop')
                            sleep(0.5)
                            tools.iferror(qt.fh_loader_err(rf'bin/{fh_loader} --port="\\.\COM{port}" --setactivepartition="0" --noprompt --showpercentagecomplete --zlpawarehost="1" --memoryname=""emmc""'),'超级恢复',status,mode='stop')
                            sleep(0.5)
                            tools.iferror(qt.fh_loader_err(rf'bin/{fh_loader} --port="\\.\COM{port}" --reset --noprompt --showpercentagecomplete --zlpawarehost="1" --memoryname=""emmc""'),'超级恢复',status,mode='stop')
                            sleep(0.5)
                            qt.exit9008()

                            log('刷入成功!')
                            status.stop()
                            input('按回车返回工具箱界面')

                        case '7.分区管理器':
                            input('本功能为高级功能,若因使用不当造成的变砖我们概不负责!')

                            log('选择mbn文件')
                            mbn = filedialog.askopenfilename(title='请选择mbn文件',filetypes=[('mbn文件','*.mbn')])
                            fh_loader = {True: 'xtcfh_loader.exe', False: 'fh_loader.exe'}[noneprompt.ConfirmPrompt('是否使用小天才加密fh_loader?',default_choice=False).prompt()]

                            status.update('等待连接')
                            status.start()
                            log('等待连接')
                            while True:
                                if adb.is_connect():
                                    adb.adb('reboot edl')
                                    break
                                if tools.check_edl():
                                    break
                            port = tools.wait_for_edl()

                            qt = tools.QT('bin/QSaharaServer.exe',f'bin/{fh_loader}',port,mbn)

                            log('进入sahara模式')
                            status.update('进入sahara模式')
                            tools.iferror(qt.intosahara(),'进入sahara模式',status,mode='stop')

                            log('获取分区列表')
                            status.update('获取分区列表')
                            partitions = qt.get_partitions_info()

                            while True:
                                part_list = [noneprompt.Choice('q.退出'),noneprompt.Choice('#.备份全部(全分区备份)'),noneprompt.Choice('#.批量写入(可用于写入备份的全分区)')]
                                for i in list(partitions.keys()):
                                    part_list.append(noneprompt.Choice(i))
                                status.stop()
                                partition = noneprompt.ListPrompt('请选择分区',part_list,default_select=2).prompt().name
                                if partition == 'q.退出':
                                    log('退出9008模式')
                                    qt.exit9008()
                                    break
                                elif partition == '#.备份全部(全分区备份)':
                                    skipuserdata = noneprompt.ConfirmPrompt('是否跳过备份Userdata?(提示:Userdata是用户数据,备份耗时较久且很占空间)',default_choice=True).prompt()
                                    if not os.path.exists('backup/'):
                                        os.mkdir('backup')
                                    status.update('读取全部分区')
                                    status.start()
                                    log('开始读取全部分区')
                                    for i in list(partitions.keys()):
                                        if i == 'userdata' and skipuserdata:
                                            log('跳过读取userdata')
                                            continue
                                        log(f'读取{i}')
                                        if i == 'system' or i == 'userdata':
                                            log(f'提示:读取{i}可能需要耗费较长的时间,请耐心等待')
                                        output = qt.read_partition(i)
                                        if not output == 'success':
                                            status.stop()
                                            tools.print_error(f'读取{i}失败!',output)
                                            qt.exit9008()
                                            input()
                                            break
                                        shutil.copy(f'{i}.img','backup/')
                                        os.remove(f'{i}.img')
                                    status.stop()
                                    input(f'读取全分区完毕!文件保存在{os.getcwd()}\\backup\n按回车回到分区界面')
                                elif partition == '#.批量写入(可用于写入备份的全分区)':
                                    log('选择文件')
                                    files = filedialog.askopenfilenames(title='选择镜像文件(提示:是多选哦)',filetypes=[('镜像文件','*.img;*.bin')])
                                    partitions = qt.get_partitions_info()

                                    log('开始批量写入')
                                    status.update('批量写入')
                                    status.start()
                                    for i in files:
                                        if i.split('/')[-1][:-4] in list(partitions.keys()):
                                            log(f'写入{i.split('/')[-1][:-4]}')
                                            output = qt.write_partition(i,i.split('/')[-1][:-4])
                                            if not output == 'success':
                                                status.stop()
                                                tools.print_error(f'刷入{i.split('/')[-1][:-4]}失败',output)
                                                tools.exit_after_enter()
                                    status.stop()
                                    log('全部刷入成功!')
                                    input('按回车回到分区管理界面')
                                else:
                                    opration = {'1.读取': 'read', '2.刷入': 'write'}[noneprompt.ListPrompt('请选择操作',[noneprompt.Choice('1.读取'),noneprompt.Choice('2.刷入')]).prompt().name]
                                    if opration == 'read':
                                        status.update(f'读取{partition}分区')
                                        status.start()
                                        log(f'开始读取{partition}分区')
                                        tools.iferror(qt.read_partition(partition),f'读取{partition}分区',status,mode='stop')
                                        status.stop()
                                        console.log('读取成功!')
                                        input(f'读取成功!读取的文件在{os.getcwd()}\n按回车回到分区管理界面')
                                    else:
                                        file = filedialog.askopenfilename(title='请选择要刷入的文件',filetypes=[('镜像文件','*.img;*.bin')])
                                        status.update(f'刷入{partition}分区')
                                        status.start()
                                        log(f'开始刷入{partition}分区')
                                        tools.iferror(qt.write_partition(file,partition),f'刷入{partition}分区',status,mode='stop')
                                        status.stop()
                                        console.log('刷入成功!')
                                        input('刷入成功!按回车回到分区管理界面')
                        case '8.进入qmmi模式':
                            input('本功能为高级功能,若因使用不当造成的变砖我们概不负责!')
                            log('选择mbn文件')
                            mbn = filedialog.askopenfilename(title='请选择mbn文件',filetypes=[('mbn文件','*.mbn')])
                            fh_loader = {True: 'xtcfh_loader.exe', False: 'fh_loader.exe'}[noneprompt.ConfirmPrompt('是否使用小天才加密fh_loader?',default_choice=False).prompt()]
                            log('等待连接')
                            status.update('等待连接')
                            status.start()
                            while True:
                                if adb.is_connect():
                                    adb.adb('reboot edl')
                                    break
                                if tools.check_edl():
                                    break
                                sleep(0.5)
                            port = tools.wait_for_edl()
                            qt = tools.QT('bin/QSaharaServer.exe',f'bin/{fh_loader}',port,mbn)
                            with open('tmp/misc.bin','w') as f:
                                f.write('ffbm-02')

                            log('进入sahara模式')
                            status.update('进入sahara模式')
                            tools.iferror(qt.intosahara(),'进入sahara模式',status,mode='stop')

                            log('刷入misc')
                            status.update('刷入misc')
                            tools.iferror(qt.write_partition('tmp/misc.bin','misc'),'刷入misc',status,mode='stop')

                            log('退出9008模式')
                            status.update('退出9008模式')
                            tools.iferror(qt.exit9008(),'退出9008模式',status,mode='stop')

                            status.stop()
                            log('已进入qmmi模式,请耐心等待开机!')
                            input('按回车返回工具箱界面')
                        case '9.设置微信QQ开机自启动':
                            if not adb.is_connect():
                                status.update('等待连接')
                                log('等待连接')
                                status.start()
                                adb.wait_for_connect()
                                adb.wait_for_complete()
                            status.update('正在执行')
                            log('正在执行')
                            adb.shell('content call --uri content://com.xtc.launcher.self.start --method METHOD_SELF_START --extra EXTRA_ENABLE:b:true --arg com.tencent.qqlite')
                            adb.shell('content call --uri content://com.xtc.launcher.self.start --method METHOD_SELF_START --extra EXTRA_ENABLE:b:true --arg com.tencent.qqwatch')
                            adb.shell('content call --uri content://com.xtc.launcher.self.start --method METHOD_SELF_START --extra EXTRA_ENABLE:b:true --arg com.tencent.wechatkids')
                            log('执行成功!')
                            status.stop()
                            input('按回车返回工具箱界面')
                        case '10.启动投屏':
                            if not adb.is_connect():
                                status.update('等待连接')
                                log('等待连接')
                                status.start()
                                adb.wait_for_connect()
                                adb.wait_for_complete()
                            subprocess.Popen('bin/scrcpy.exe',stderr=subprocess.STDOUT,stdout=subprocess.PIPE)
                            log('执行成功!')
                            input('按回车返回工具箱界面')

            case '4.关于':
                os.system('cls')
                tools.print_logo(version)
                print('')
                about = '''XTCEasyRootPlus是一个使用Python制作的小天才电话手表一键Root程序
    本项目以GPL协议开源在Github:https://www.github.com/OnesoftQwQ/XTCEasyRootPlus

    作者:
        [red]花火玩偶[/red] 和 [blue]Onesoft[/blue]

    特别鸣谢:
        早茶光: 制作了XTCEasyRoot,xtcpatch,810和711的adbd,多个版本的改版桌面,并且为我解答了许多问题,[white]本项目的逻辑基本上是参考[/white][strike](抄)[/strike]的XTCEasyRoot
        huanli233: 制作了部分改版桌面,notice,systemplus,weichatpro2'''

                for i in about.splitlines():
                    print(i)
                    sleep(0.5)

                input('\n按回车回到主界面......')

except Exception as e:
    tools.logging(traceback.format_exc())
    raise e