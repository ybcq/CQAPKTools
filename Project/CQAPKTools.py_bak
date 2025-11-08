#from operator import length_hint
#from tkinter.tix import Tree
import PySimpleGUI as sg
import os
#import subprocess
import configparser
#import pyperclip
import codecs

curpath=os.path.dirname(os.path.realpath(__file__))
cfgpath=os.path.join(curpath,"CQApkRename.ini")
exepath=os.path.join(curpath,"CQApkRename.exe")
batpath=os.path.join(curpath,"HuaweiSubstW.bat")
lnkpath=os.path.join(curpath,"HuaweiSubstW.lnk")
apkpath=os.path.join(curpath,"ApkInstaller.exe")

class NewConfigParser(configparser.ConfigParser):
    def optionxform(self,optionstr):
        return optionstr

# 创建管理对象
conf=NewConfigParser()
 
# 读ini文件
conf.read(cfgpath,encoding="utf-8")  # python3
aaptPath=conf.get("Config","aaptPath")
keytoolPath=conf.get("Config","keytoolPath")
newFileNamePattern=conf.get("Config","newFileNamePattern")

sg.theme('GreenTan')# Add a little color to your windows
sg.set_options(font=("等线",10))

#主窗口
layout_choose=[
            [sg.Button('MIUI优化'),sg.Button("华为引擎")],
            [sg.Button("批量命名"),sg.Button("其他功能")]
        ]

layout_about=[
            [sg.Button('关于软件'),sg.Button('作者官网')]
        ]

layout=[[sg.Frame("选择",layout_choose)],
        [sg.Frame("关于",layout_about)],
]

window_main=sg.Window('',layout)

miui_active=False
huawei_active=False
rename_active=False
other_active=False

# 冻结子函数，True为解冻，False为冻结
def apkchange(state, name):
    if state == True:
        st="enable"
    else:
        st="disable-user"

    r=os.popen('adb shell pm ' + st + " " + name).read()
    if r.find(st):
        t="成功"
    else:
        t="失败"
    sg.Popup('已发送命令，返回值为：',r,title=t)

# 调整动画子函数，
def dhchange(sulv):
    os.popen('adb shell settings put global window_animation_scale ' + sulv).read()
    os.popen('adb shell settings put global transition_animation_scale ' + sulv).read()
    os.popen('adb shell settings put global animator_duration_scale ' + sulv).read()

# Create the event loop
while True:
    event,values=window_main.read()

    if event in (None,'Close'):
        break
    elif event in (None,'MIUI优化') and not miui_active:
        miui_active=True
        window_main.hide()

        #MIUI优化窗口布局
        miui_icebox=[
            [sg.Text("以下冻结的应用是在尽可能保留系统正常功能的情况下释放内存占用的列表，不是激进冻结列表")],
            [sg.Text("如果需要自由冻结应用，请自行使用 adb shell pm disable-user + 包名 或搞机工具箱",)],
            # [sg.Text("")],
            [sg.Button('冻结Analytics'),sg.Button('解冻Analytics'),sg.Text("分析服务，通常无用")],
            [sg.Button("冻结Adsolution"),sg.Button("解冻Adsolution"),sg.Text("广告服务，冻结可减少广告")],
            [sg.Button("冻结Joyose"),sg.Button("解冻Joyose"),sg.Text("温控服务，冻结可能影响计步")],
            [sg.Button("冻结SIM STK"),sg.Button("解冻SIM STK"),sg.Text("SIM卡服务，通常无用")],
            [sg.Button("冻结内容中心"),sg.Button("解冻内容中心"),sg.Text("桌面上滑的新闻，通常无用")],
            [sg.Button("冻结快应用"),sg.Button("解冻快应用"),sg.Text("快应用服务框架，通常无用")],
            [sg.Button("冻结电量与性能"),sg.Button("解冻电量与性能"),sg.Text("冻结可开启全局高刷，会导致耗电更快")],
            [sg.Button("卸载系统更新"),sg.Button("还原系统更新"),sg.Text("解锁ID机专用")],
            [sg.Text("")],
            [sg.Button("一键冻结"),sg.Button("一键解冻"),sg.Text("冻结和解冻除了电量与性能以外的所有项")],
        ]

        miui_catoon=[
            [sg.Button('无动画'),sg.Button('快速'),sg.Button('默认设置'),sg.Button("优雅"),sg.Text("该设置会影响所有系统动画")]
        ]

        miui_better=[
            [sg.Button('无后台'),sg.Button('激进'),sg.Button('轻快'),sg.Button("默认限制"),sg.Text("该设置可能会引起微信后台不稳定，推荐在备用机上使用")]
        ]

        miui=[[sg.Frame("冻结提速",miui_icebox)],
                [sg.Frame("动画设置",miui_catoon)],
                [sg.Frame("后台策略",miui_better)]
        ]

        window_miui=sg.Window('MIUI工具箱',miui)

        while True:
            ev_miui, val_miui=window_miui.read()
            if ev_miui in (None,'Close'):
                window_miui.close()
                miui_active=False
                window_main.UnHide()
                break
            elif ev_miui in (None,'冻结Analytics'):
                apkchange(False, "com.miui.analytics")

            elif ev_miui in (None,'解冻Analytics'):
                apkchange(True, "com.miui.analytics")

            elif ev_miui in (None,'冻结Joyose'):
                apkchange(False, "com.xiaomi.joyose")

            elif ev_miui in (None,'解冻Joyose'):
                apkchange(True, "com.xiaomi.joyose")

            elif ev_miui in (None,'冻结Adsolution'):
                apkchange(False, "com.miui.systemAdSolution")

            elif ev_miui in (None,'解冻Adsolution'):
                apkchange(True, "com.miui.systemAdSolution")

            elif ev_miui in (None,'冻结SIM STK'):
                apkchange(False, "com.android.stk")

            elif ev_miui in (None,'解冻SIM STK'):
                apkchange(True, "com.android.stk")

            elif ev_miui in (None,'冻结快应用'):
                apkchange(False, "com.miui.hybrid")

            elif ev_miui in (None,'解冻快应用'):
                apkchange(True, "com.miui.hybrid")

            elif ev_miui in (None,'冻结内容中心'):
                apkchange(False, "com.miui.newhome")

            elif ev_miui in (None,'解冻内容中心'):
                apkchange(True, "com.miui.newhome")

            elif ev_miui in (None,'冻结电量与性能'):
                apkchange(False, "com.miui.powerkeeper")

            elif ev_miui in (None,'解冻电量与性能'):
                apkchange(False, "com.miui.powerkeeper")
            
            elif ev_miui in (None,'卸载系统更新'):
                st="Success"
                t="成功"
                r=os.popen('adb shell pm uninstall --user 0 com.android.updater').read()
                if not r.find(st):
                    t="失败"
                    
            elif ev_miui in (None,'还原系统更新'):
                st="Success"
                t="成功"
                r=os.popen('adb shell pm install --user 0 com.android.updater').read()
                if not r.find(st):
                    t="失败"

            elif ev_miui in (None,'一键冻结'):
                st="disable-user"
                t="成功"
                r=os.popen('adb shell pm ' + st + " " + "com.miui.analytics").read()
                if not r.find(st):
                    t="失败"
                r=os.popen('adb shell pm ' + st + " " + "com.xiaomi.joyose").read()
                if not r.find(st):
                    t="失败"
                r=os.popen('adb shell pm ' + st + " " + "com.miui.systemAdSolution").read()
                if not r.find(st):
                    t="失败"
                r=os.popen('adb shell pm ' + st + " " + "com.android.stk").read()
                if not r.find(st):
                    t="失败"
                r=os.popen('adb shell pm ' + st + " " + "com.miui.hybrid").read()
                if not r.find(st):
                    t="失败"
                r=os.popen('adb shell pm ' + st + " " + "com.miui.newhome").read()
                if not r.find(st):
                    t="失败"
                
                sg.Popup('已尝试一键冻结！结果为：',t,title=t)

            elif ev_miui in (None,'一键解冻'):
                st="enable"
                t="成功"
                r=os.popen('adb shell pm ' + st + " " + "com.miui.analytics").read()
                if not r.find(st):
                    t="失败"
                r=os.popen('adb shell pm ' + st + " " + "com.xiaomi.joyose").read()
                if not r.find(st):
                    t="失败"
                r=os.popen('adb shell pm ' + st + " " + "com.miui.systemAdSolution").read()
                if not r.find(st):
                    t="失败"
                r=os.popen('adb shell pm ' + st + " " + "com.android.stk").read()
                if not r.find(st):
                    t="失败"
                r=os.popen('adb shell pm ' + st + " " + "com.miui.hybrid").read()
                if not r.find(st):
                    t="失败"
                r=os.popen('adb shell pm ' + st + " " + "com.miui.newhome").read()
                if not r.find(st):
                    t="失败"
                r=os.popen('adb shell pm ' + st + " " + "com.miui.powerkeeper").read()
                if not r.find(st):
                    t="失败"
                
                sg.Popup('已尝试一键解冻！结果为：',t,title=t)

            elif ev_miui in (None,'无动画'):
                r=dhchange("0")
                sg.Popup('已调节动画为：无动画。',r,title="成功")

            elif ev_miui in (None,'快速'):
                r=dhchange("0.5")
                sg.Popup('已调节动画为：快速。',r,title="成功")

            elif ev_miui in (None,'默认设置'):
                r=dhchange("1")
                sg.Popup('已调节动画为：默认设置。',r,title="成功")

            elif ev_miui in (None,'优雅'):
                r=dhchange("1.5")
                sg.Popup('已调节动画为：优雅。',r,title="成功")

            elif ev_miui in (None,'无后台'):
                os.popen('adb shell settings put global activity_manager_constants max_cached_processes=0')
                r=os.popen('adb shell get settings put global activity_manager_constants').read()
                sg.Popup('已更改后台机制为：无后台。',r,title="成功")

            elif ev_miui in (None,'激进'):
                os.popen('adb shell settings put global activity_manager_constants max_cached_processes=1')
                r=os.popen('adb shell get settings put global activity_manager_constants').read()
                sg.Popup('已更改后台机制为：激进。',r,title="成功")

            elif ev_miui in (None,'轻快'):
                os.popen('adb shell settings put global activity_manager_constants max_cached_processes=4')
                r=os.popen('adb shell get settings put global activity_manager_constants').read()
                sg.Popup('已更改后台机制为：轻快。',r,title="成功")

            elif ev_miui in (None,'默认限制'):
                os.popen('adb shell settings put global activity_manager_constants max_cached_processes=16')
                r=os.popen('adb shell get settings put global activity_manager_constants').read()
                sg.Popup('已更改后台机制为：默认限制。',r,title="成功")

    elif event in (None,'华为引擎') and not huawei_active:
        huawei_active=True
        window_main.hide()

        #华为引擎窗口布局
        huawei_disk=[
                    [sg.Text("用于把华为移动应用引擎的共享目录映射为盘符，方便传入传出文件")],
                    [sg.Text("方法1：")],
                    [sg.Button('映射共享目录为W盘'),sg.Button('取消映射共享磁盘'),sg.Button("设置开机自动映射共享目录")],
                    [sg.Text("方法2：")],
                    [sg.Button("使用网络路径方式创建共享目录图标")]
        ]

        huawei_other=[
            [sg.Button('安装华为移动引擎'),sg.Text("跳转到心某人的网站")],
            [sg.Button('杀死华为移动引擎'),sg.Text("用于华为移动应用引擎卡死后或不再使用时释放内存")],
            [sg.Button('为华为移动引擎安装软件'),sg.Text("打开汉化版的ApkInstaller")],
        ]

        huawei=[[sg.Frame("共享磁盘",huawei_disk)],
                [sg.Frame("其他功能",huawei_other)],
        ]

        window_huawei=sg.Window('华为移动应用引擎工具箱',huawei)

        while True:
            ev_huawei, val_huawei=window_huawei.read()
            if ev_huawei in (None,'Close'):
                window_huawei.close()
                huawei_active=False
                window_main.UnHide()
                break
            elif ev_huawei in (None,'映射共享目录为W盘'):
                os.popen('subst w: %appdata%\Huawei\Emulator\Share')
                sg.Popup('已成功映射共享目录为W盘，如果不显示就多刷新几下。',title='成功')
                os.popen('explorer')

            elif ev_huawei in (None,'取消映射共享磁盘'):
                os.popen('subst w: /d')
                sg.Popup('已取消映射华为移动应用引擎到W盘！',title='成功')
            
            elif ev_huawei in (None,'设置开机自动映射共享目录'):
                os.popen(r'xcopy "'+batpath+r'" "%appdata%\Microsoft\Windows\Start Menu\Programs\Startup"')
                sg.Popup('已成功设置开机自动映射共享目录。',title='成功')

            elif ev_huawei in (None,'使用网络路径方式创建共享目录图标'):
                os.popen(r'copy "'+lnkpath+r'" "%appdata%\Microsoft\Windows\Network Shortcuts\安卓磁盘 (W).lnk"')
                sg.Popup('已成功使用网络路径方式创建共享目录图标。',title='成功')
                os.popen('explorer')

            elif ev_huawei in (None,'安装华为移动引擎'):
                os.popen('explorer https://space.bilibili.com/28516198')

            elif ev_huawei in (None,'杀死华为移动引擎'):
                os.popen('taskkill /f /im MobileAppEngine.exe')
                sg.Popup('已关闭华为应用引擎',title="成功")

            elif ev_huawei in (None,'为华为移动引擎安装软件'):
                try:
                    os.popen('call "' + apkpath + '"')
                    #r=os.popen('start ' + apkpath).read()
                    #if r.find("拒绝"):
                        #sg.Popup('权限不足，请使用管理员身份运行该软件',title='权限不足')
                except:
                    sg.Popup('请使用管理员身份运行该软件',title='权限不足')

    elif event in (None,'批量命名') and not rename_active:
        rename_active=True
        window_main.hide()

        #批量重命名窗口布局
        rename_path=[
                    [sg.Text("选择单文件"),sg.InputText(key='file'),sg.FileBrowse(button_text="...",key='file',)],
                    [sg.Text("选择文件夹"),sg.InputText(key='path'),sg.FolderBrowse(button_text="...",key='path')]
        ]

        rename_set=[
                    [sg.Text("表达式：{应用包名} {应用名字} {版本名字} {APP证书用户} {APP证书序列号}")],
                    [sg.InputText(key='kind',default_text=newFileNamePattern),],
                    [sg.Button('应用设置'),sg.Button("关联到右键菜单"),sg.Button("删除右键菜单")]
        ]

        rename=[[sg.Frame("重命名操作",rename_path),sg.Button('开始重命名')],
                [sg.Frame("重命名设置",rename_set)],
        ]

        window_rename=sg.Window('批量命名APK文件',rename)

        while True:
            ev_rename, val_rename=window_rename.read()
            if ev_rename in (None,'Close'):
                window_rename.close()
                rename_active=False
                window_main.UnHide()
                break

            elif ev_rename in (None,'开始重命名'):
                # User closed the Window or hit the Cancel button
                # 单文件
                print(val_rename['file'])
                try:
                    filepath=val_rename['file']
                except:
                    break
                # print(filepath)
                if filepath != None:
                    if os.path.exists(filepath):
                        os.popen(f'"{exepath}"' + ' "'+ filepath + '"')
                

                # 多文件
                pathpath=val_rename['path']
                s="" #路径整合
                if pathpath != None:
                    if os.path.exists(pathpath):
                        for root,dirs,files in os.walk(pathpath):
                            for file in files: 
                                apkpath=os.path.join(root,file)
                                # print (apkpath)
                                if apkpath.endswith("apk"):
                                    apkpath=apkpath.replace('/','\\')
                                    s=s + '"' + apkpath + '" '
                        print(f'"{exepath}"' + ' '+ s)
                        os.popen(f'"{exepath}"' + ' '+ s) 
            
            elif ev_rename in (None,'应用设置'):
                setpath=val_rename['kind']
                conf.set("Config","newFileNamePattern",setpath)
                conf.write(codecs.open(cfgpath,"w","utf-8"))
                sg.Popup('已成功修改设置为：',setpath,title='成功')
            
            elif ev_rename in (None,'关联到右键菜单'): 
                # 使用RegOpenKey打开注册表项  
                try:
                    r=os.popen(f'reg add "HKEY_CLASSES_ROOT\SystemFileAssociations\.apk\shell\用 CQApkTools 重命名...\command" /ve /t REG_SZ /d "\\"{exepath}\\" \\"%1\\"" /f').read()
                    if r.find("拒绝"):
                        sg.Popup('权限不足，请使用管理员身份运行该软件',title='权限不足')
                    else:
                        sg.Popup('已成功加入安装包的右键菜单',title='成功')
                except:
                    break    
        
            elif ev_rename in (None,'删除右键菜单'): 
                # 使用RegOpenKey打开注册表项  
                try:
                    r=os.popen('reg delete "HKEY_CLASSES_ROOT\SystemFileAssociations\.apk\shell\用 CQApkTools 重命名..." /f').read()
                    if r.find("拒绝"):
                        sg.Popup('权限不足，请使用管理员身份运行该软件',title='权限不足')
                    else:
                        sg.Popup('已成功删除安装包的右键菜单',title='成功')
                except:
                    break

    elif event in (None,'其他功能') and not other_active:
        other_active=True
        window_main.hide()

        #其他快捷操作窗口布局
        other_adb=[
            [sg.Button("激活女娲石"),sg.Text("同步移除")],
            [sg.Button("激活小黑屋"),sg.Text("麦克斯韦妖模式")],
            [sg.Button("激活Shizuku"),sg.Text("比无线调试更稳定")],
            [sg.Button("激活Scene5"),sg.Text("手机管理工具")],
            #[sg.Button("激活爱玩机工具箱"),sg.Text("尚未实现")],
        ]

        other=[[sg.Frame("ADB激活",other_adb)],
        ]
        window_other=sg.Window('其他快捷操作',other)

        while True:
            ev_other, val_other=window_other.read()
            if ev_other in (None,'Close'):
                window_other.close()
                other_active=False
                window_main.UnHide()
                break

            if ev_other in (None,'激活女娲石'):
                r1=os.popen('adb shell setprop persist.log.tag.NotificationService DEBUGsetprop persist.log.tag.NotificationService DEBUG').read()
                r2=os.popen('adb shell pm grant com.oasisfeng.nevo android.permission.READ_LOGS').read()
                sg.Popup('已尝试激活，返回值为：',r1+r2,title="成功")

            if ev_other in (None,'激活小黑屋'):
                r=os.popen('adb shell sh /storage/emulated/0/Android/data/web1n.stopapp/files/starter.sh').readlines()[-1]
                sg.Popup('已尝试激活，返回值为：',r,title="成功")

            if ev_other in (None,'激活Shizuku'):
                r=os.popen('adb shell sh /storage/emulated/0/Android/data/moe.shizuku.privileged.api/start.sh').read()
                sg.Popup('已尝试激活，返回值为：',r,title="成功")

            if ev_other in (None,'激活Scene5'):
                r=os.popen('adb shell sh /data/user/0/com.omarea.vtools/files/up.sh').read()
                sg.Popup('已尝试激活，返回值为：',r,title="成功")

            #if ev_other in (None,'激活爱玩机工具箱'):
                # r=os.popen('adb shell settings put global activity_manager_constants max_cached_processes=16').read()
                # sg.Popup('已尝试激活，返回值为：',r,title="成功")

    elif event in (None,'关于软件'):
        sg.Popup("CQApkTools Ver 2.0","CQApkTools不是一个原创工具，而是一个整合工具。","其中","ApkRenamer 的作者是 AsionTang","ApkInstaller 的汉化者是 御坂初琴","",'御坂初琴软件屋',"https://ybcq.github.io/","CopyRight By Misaka HatSune 2020-2025",title="关于")

    elif event in (None,'作者官网'):
        os.popen('explorer https://ybcq.github.io/')


window_main.close()