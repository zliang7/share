#! N:\Python27\python.exe
# -*- coding: utf-8 -*-

#

import re
import os
import datetime
import argparse
import platform
import sys
import commands

system = platform.system()
root_dir = '/workspace/project/android/skia/'
src_dir = root_dir + 'trunk/'
platform_tools_dir = src_dir + 'platform_tools/'
log_dir = '/workspace/topic/skia/log/'
log_suffix = '.txt'
config = ['8888', '565', 'GPU', 'NULLGPU']
NA = 'NA'
target = ''

android_sdk_root = '/workspace/topic/skia/adt-bundle-linux-x86_64/sdk'

def info(msg):
    print "[INFO] " + msg + "."

def error(msg):
    print "[ERROR] " + msg + "!"

def cmd(msg):
    print '[COMMAND] ' + msg

def execute(command):
    cmd(command)
    if os.system(command):
        error('Failed to execute')
        quit()

def avg(self):
        if len(self.sequence) < 1:
            return None
        else:
            return sum(self.sequence) / len(self.sequence)

def get_data(name, result):
    for item in result:
        if item[0] == name:
            data = map(float, item[1].split(','))
            avg = sum(data) / len(data)
            return '%.2f' %avg

    return NA

def get_datetime():
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d%H%M%S")

def _parse_format_result(log_file, base):
    fr = open(log_dir + log_file)
    lines = fr.readlines()
    fr.close()

    for line in lines:
        if re.match('^\s+$', line):
            continue
        p = re.compile('\S+')
        base.append(re.findall(p, line))

def _compare_result(files):
    #f = files.split(',')

    file_number = len(f)
    base = []
    total = []
    _parse_format_result(f[0], base)
    _parse_format_result(f[0], total)

    for i in range(1, file_number):
        print '== ' + f[0] + ' vs. ' + f[i] + ' =='
        compare = []
        parse_format_result(f[i], compare)

        for i in range(len(base)):
            if base[i][0] != compare[i][0]:
                error('Result can\'t be compared')
                quit()
            else:
                s = ''
                diff = []
                for j in range(1, len(base[i])):
                    if base[i][j] == NA or compare[i][j] == NA:
                        total[i][j] = NA
                        if base[i][j] == compare[i][j]:
                            continue

                        if s != '':
                            s = s + ' '
                        s = s + config[j - 1] + ':' + base[i][j] + '->' + compare[i][j]

                    else:
                        b = float(base[i][j])
                        c = float(compare[i][j])
                        d = (b - c) / b
                        total[i][j] = float(total[i][j]) + c
                        if abs(d) < 0.05:
                            continue

                        if s != '':
                            s = s + ' '
                        s = s + config[j - 1] + ':' + base[i][j] + '->' + compare[i][j] + '(' + ('%.2f' %(d * 100)) + '%)'

                if s != '':
                    print base[i][0] + ' ' + s

        print ''

    # Print average
    print '== Average =='
    for i in range(len(total)):
        s = ''
        for j in range(1, len(total[i])):
        #for j in range(3, 4):
            if total[i][j] == NA:
                s = s + ' NA'
            else:
                s = s + ' ' + ('%.2f' %(total[i][j] / file_number))
        s = total[i][0] + s
        print s

def parse_result(log_file):
    fr = open(log_dir + log_file + log_suffix)
    lines = fr.readlines()
    fr.close()

    fw = open(log_dir + log_file + '_format' + log_suffix, 'w')
    for line in lines:
        if re.match('^running bench', line):
            p = re.compile('^running bench \[640 480\]\s+(\S+)\s+')
            m = re.match(p, line)
            s = m.group(1)
            p = re.compile('(8888|565|GPU|NULLGPU):.+?cmsecs =\s+(\S+)\s')
            m = re.findall(p, line)
            for i in range(len(config)):
                s = s + ' ' + get_data(config[i], m)
            fw.write(s + '\n')
    fw.close()

def run(args):
    if not args.run:
        return()

    if not args.device:
        error('Please designate device to run with')
        quit()

    device_found = False
    command = 'adb devices -l'
    devices = commands.getoutput(command).split('\n')
    for device in devices:
        if device[:len(args.device)] == args.device:
            device_found = True
            break

    if not device_found:
        error('Device is not connected')
        quit()

    execute('echo out/config/android-' + target + ' > ' + src_dir + '.android_config')

    format_files = ''

    os.chdir(src_dir)
    if args.run_nonroot:
        execute('platform_tools/android/bin/android_install_skia --release -s ' + args.device)
        if args.bench_option:
            command = 'platform_tools/android/bin/android_run_skia --intent "bench --repeat 20 ' + args.bench_option + '"'
        else:
            command = 'platform_tools/android/bin/android_run_skia --intent "bench --repeat 20"'
    else:
        execute('platform_tools/android/bin/android_install_skia --release --install-launcher -s ' + args.device)
        execute('platform_tools/android/bin/linux/adb shell stop')
        command = 'platform_tools/android/bin/android_run_skia bench --repeat 20'
        if args.bench_option:
            command = command + ' ' + args.bench_option


    log_file = get_datetime() + '_' + args.device + '_bench'
    command = command + ' 2>&1 |tee '+ log_dir + log_file + '.txt'
    execute(command)

    if not args.run_nonroot:
        execute('platform_tools/android/bin/linux/adb shell start')

    parse_result(log_file)

def build(args):
    if not args.build:
        return()

    os.putenv('ANDROID_SDK_ROOT', android_sdk_root)

    if args.build.upper() == 'DEBUG':
        build = 'Debug'
    elif args.build.upper() == 'RELEASE':
        build = 'Release'
    elif args.build.upper() == 'ALL':
        build = 'All'

    print '== Build Environment =='
    print 'Directory of src: ' + src_dir
    print 'Build type: ' + build
    print 'System: ' + system
    print '======================='

    os.chdir(src_dir)

    if build == 'Debug' or build == 'All':
        execute('platform_tools/android/bin/android_make -d ' + target + ' -j BUILDTYPE=Debug')

    if build == 'Release' or build == 'All':
        execute('platform_tools/android/bin/android_make -d ' + target + ' -j BUILDTYPE=Release')

def set_target(args):
    global target
    if not args.build and not args.run:
        return()

    target_from_option = ''
    if args.target == 'x86':
        target_from_option = 'x86'
    elif args.target == 's3':
        target_from_option = 'nexus_4'
    elif args.target = 'nexus_4':
        target_from_option = 'nexus_4'

    target_from_device = ''
    # Guess target from 'adb devices -l'
    command = 'adb devices -l'
    devices = commands.getoutput(command).split('\n')
    for device in devices:
        if device[:len(args.device)] == args.device:
            if re.search('Medfield', device):
                target_from_device = 'x86'
            elif re.search('Nexus_4', device):
                target_from_device = 'nexus_4'
            break

    # Add some manual map here
    if target_from_device == '':
        if args.device == '32300bd273508f3b':
            target_from_device = 'nexus_4'

    if target_from_device != '' and target_from_option != '' and target_from_device != target_from_option:
        error('Device could not match target. ' + 'target_from_device: ' + target_from_device + ' target_from_option: ' + target_from_option)
        quit()

    if target_from_device == '' and target_from_option == '':
        error('Either device or target should be designated')
        quit()

    if target_from_device != '':
        target = target_from_device

    if target_from_option != '':
        target = target_from_option

def update(args):
    if not args.update:
        return()

    os.chdir(root_dir)
    execute('gclient ' + args.update)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Script to update, build and run Skia for Android IA',
                                     formatter_class = argparse.RawTextHelpFormatter,
                                     epilog = '''
examples:

  update:
  python %(prog)s -u sync
  python %(prog)s -u 'sync --force'

  build:
  python %(prog)s -b release
  python %(prog)s -b release -t s3
  python %(prog)s -b all

  run:
  python %(prog)s -r release -d 32300bd273508f3b // s3
  python %(prog)s -r release -d 006e7e464bd64fef // nexus 4
  python %(prog)s -r release --run-nonroot -d 32300bd273508f3b --bench-option '--match region_contains_sect --match verts'
  python %(prog)s -r release -d Medfield6CCF763B // pr2
  python %(prog)s -r release -d Medfield6CCF763B --bench-option '--match region_contains_sect --match verts'


  update & build & run
  python %(prog)s -u sync -b release -r release -d Medfield6CCF763B
''')

    groupUpdate = parser.add_argument_group('update')
    groupUpdate.add_argument('-u', '--update', dest='update', help='gclient options to update source code')

    groupUpdate = parser.add_argument_group('build')
    groupUpdate.add_argument('-b', '--build', dest='build', help='type to build', choices=['release', 'debug', 'all'])
    groupUpdate.add_argument('-t', '--target', dest='target', help='target', choices=['x86', 's3', 'nexus_4'])

    groupUpdate = parser.add_argument_group('run')
    groupUpdate.add_argument('-r', '--run', dest='run', help='type to run', choices=['release', 'debug'])
    groupUpdate.add_argument('-d', '--device', dest='device', help='device id')
    groupUpdate.add_argument('--run-nonroot', dest='run_nonroot', help='run without root access, which would not install skia_launcher to /system', action='store_true')
    groupUpdate.add_argument("--bench-option", dest="bench_option", help="option to run bench test", default='')

    parser.add_argument("-p", "--parse-result", dest="parse_result", help="Parse result file", default='')
    parser.add_argument("-c", "--compare-result", dest="compare_result", help="Compare result file", default='')

    groupUpdate = parser.add_argument_group('other')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()

    update(args)
    set_target(args)
    build(args)
    run(args)
    #parse_result(args)
    #compare_result(args)


