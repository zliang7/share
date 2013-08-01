#! N:\Python27\python.exe
# -*- coding: utf-8 -*-

import re
import os
import datetime
import argparse
import platform
import sys
import commands
import time
import urllib2
from httplib import BadStatusLine

system = platform.system()
log_suffix = '.txt'
config = ['8888', '565', 'GPU', 'NULLGPU', 'NONRENDERING']
config_concerned = [0, 0, 1, 0, 1]
NA = 'NA'
target = ''
root_dir = ''
log_dir = ''
src_dir = ''
platform_tools_dir = ''
android_sdk_root = '/workspace/topic/skia/adt-bundle-linux-x86_64/sdk'
saved_dir = ''
root_dir_default = '/workspace/project/skia/'
log_dir_default = '/workspace/topic/skia/log/'

SMALL_NUMBER = 0.000001
LARGE_NUMBER = 10000

def info(msg):
    print "[INFO] " + msg + "."

def error(msg):
    print "[ERROR] " + msg + "!"

def cmd(msg):
    print '[COMMAND] ' + msg

def backup_dir(new_dir):
    global saved_dir
    saved_dir = os.getcwd()
    os.chdir(new_dir)

def restore_dir():
    os.chdir(saved_dir)

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

def _parse_format_result(dir, log_file, results):
    backup_dir(dir)
    fr = open(log_file)
    lines = fr.readlines()
    fr.close()

    for line in lines:
        # Skip blank line
        if re.match('^\s+$', line):
            continue
        # Skip title
        if re.match('Name 8888 565 GPU NULLGPU NONRENDERING', line):
            continue

        p = re.compile('\S+')
        results.append(re.findall(p, line))

    restore_dir()

def average(average_dir):
    backup_dir(log_dir)
    total_result = []
    total_number = 0

    files = os.listdir(average_dir)
    for file in files:
        if not re.search('format', file):
            continue

        total_number += 1
        if total_number == 1:
            _parse_format_result(average_dir, file, total_result)
            continue

        temp_result = []
        _parse_format_result(average_dir, file, temp_result)

        for i in range(len(temp_result)):
            if temp_result[i][0] != total_result[i][0]:
                error('Results to calculate average do not have same format')
                quit()

            for j in range(1, len(config) + 1):
                if temp_result[i][j] == 'NA' or total_result[i][j] == 'NA':
                    total_result[i][j] = 'NA'
                    if temp_result[i][j] != total_result[i][j]:
                        error('One of result is NA, while the other is not')
                        quit()
                else:
                    total_result[i][j] = float(total_result[i][j]) + float(temp_result[i][j])

    dirs = average_dir.split('/')
    if dirs[-1] == '':
        dir_name = dirs[-2]
    else:
        dir_name = dirs[-1]
    fw = open(average_dir + '/' + dir_name + '-average' + log_suffix, 'w')
    fw.write('Name ' + ' '.join(config) + '\n')
    for r in total_result:
        s = r[0]
        for i in range(1, len(config) + 1):
            if r[i] == 'NA':
                s += ' NA'
            else:
                s += ' ' + str(r[i] / total_number)
        s += '\n'
        fw.write(s)
    fw.close()

    restore_dir()

def download(args):
    if not args.download:
        return()


    if args.download not in ['nexus10', 'nexus4']:
        error('Device to download is supported now')
        quit()

    # Get latest build number
    url = 'http://108.170.217.252:10117/console?reload=40&repository=http://skia.googlecode.com/svn&revs=20&limit=50&category=Perf|Android'
    try:
        u = urllib2.urlopen(url)
    except BadStatusLine:
        error('Failed to visit waterfall')

    html = u.read()
    pattern = re.compile('Perf-Android-Nexus10-MaliT604-Arm7-Release&number=(\d+)')
    match = pattern.search(html)
    build_number = match.group(1)

    # Get log for specific build number
    if args.download == 'nexus10':
        link = 'Nexus10-MaliT604'
    elif args.download == 'nexus4':
        link = 'Nexus4-Adreno320'
    origin_file = log_dir + link + '-Arm7-' + str(build_number) + '-bench-origin' + log_suffix

    if os.path.exists(origin_file):
        info(origin_file + ' has been downloaded')
        return()

    url = 'http://108.170.217.252:10117/builders/Perf-Android-' + link + '-Arm7-Release/builds/' + build_number + '/steps/RunBench/logs/stdio/text'
    try:
        u = urllib2.urlopen(url)
    except BadStatusLine:
        error('Failed to get results of ' + args.download + ' with build number ' + build_number)

    fw = open(origin_file, 'w')
    for line in u:
        fw.write(line)
    fw.close()


    # Format origin log
    fr = open(origin_file)
    lines = fr.readlines()
    fr.close()

    format_file = origin_file.replace('origin', 'format')

    if os.path.exists(format_file):
        os.remove(format_file)

    fw = open(format_file, 'w')
    fw.write('Name ' + ' '.join(config) + '\n')
    for line_index in range(0, len(lines)):
        if re.search('beginning of /dev/log/main', lines[line_index]):
            break

        if re.search('running bench', lines[line_index]):
            p = re.compile('running bench \[\d+ \d+\]\s+(\S+)')
            m = re.search(p, lines[line_index])
            s = m.group(1)
            pattern = re.compile('(' + '|'.join(config) + '):.+?cmsecs =\s+([^ \t\n\r\f\v[a-zA-Z]*)[a-zA-Z]*\s*')
            matches = re.findall(pattern, lines[line_index])
            if matches[0][0] == '8888':
                while len(matches) < 4:
                    line_index += 1
                    # Skip error lines
                    while re.search('\] Skia Error', lines[line_index]):
                        line_index += 1
                    m = re.findall(pattern, lines[line_index])
                    matches.append(m)

            for i in range(len(config)):
                s = s + ' ' + get_data(config[i], matches)
            fw.write(s + '\n')
    fw.close()

def _item_in_list(item, list):
    for i in range(len(list)):
        if item == list[i][0]:
            return True

    return False

def compare(args):
    if not args.compare:
        return()

    diffs = []
    for i in range(len(config)):
        diffs.append([])

    files = args.compare.split(',')

    file_number = len(files)
    base = []
    _parse_format_result(log_dir, files[0], base)

    for i in range(1, file_number):
        compared = []
        _parse_format_result(log_dir, files[i], compared)

        base_index = 0
        compared_index = 0
        while base_index < len(base) and compared_index < len(compared):
            if base[base_index][0] != compared[compared_index][0]:
                base_in_compared = _item_in_list(base[base_index][0], compared)
                compared_in_base = _item_in_list(compared[compared_index][0], base)

                if base_in_compared and compared_in_base:
                    error('Base and compared data have different order')
                    quit()

                if base_in_compared:
                    base_index += 1
                else:
                    compared_index += 1
            else:
                for j in range(1, len(config) + 1):
                    if base[base_index][j] == NA or compared[compared_index][j] == NA:
                        if base[base_index][j] == compared[compared_index][j]:
                            continue

                        diffs[j - 1].append((base[base_index][0], LARGE_NUMBER, base[base_index][j], compared[compared_index][j]))

                    else:
                        b = float(base[base_index][j])
                        if b < SMALL_NUMBER:
                            b = SMALL_NUMBER
                        c = float(compared[compared_index][j])
                        if c < SMALL_NUMBER:
                            c = SMALL_NUMBER
                        d = round((c - b) / b, 4)
                        if abs(d) < 0.05:
                            continue

                        diffs[j - 1].append((base[base_index][0], d, base[base_index][j], compared[compared_index][j]))

                base_index += 1
                compared_index += 1

    for i in range(len(config)):
        diffs[i] = sorted(diffs[i], key=lambda x: x[1], reverse=True)

    # Print the sorted diff
    for i in range(len(config)):
        if not config_concerned[i]:
            continue

        print config[i] + ' ' + '% ' + files[0] + ' ' + files[1]
        for j in range(len(diffs[i])):
            print diffs[i][j][0] + ' ' + ('%.2f' %(diffs[i][j][1] * 100)) + ' ' + diffs[i][j][2] + ' ' + diffs[i][j][3]

def parse_result(dir, log_file):
    backup_dir(dir)
    format_file = log_file.replace('origin', 'format')

    if os.path.exists(format_file):
        os.remove(format_file)

    fr = open(log_file)
    lines = fr.readlines()
    fr.close()

    fw = open(format_file, 'w')
    fw.write('Name ' + ' '.join(config) + '\n')
    for line in lines:
        if re.match('^running bench', line):
            p = re.compile('^running bench \[\d+ \d+\]\s+(\S+)\s+')
            matches = re.match(p, line)
            s = matches.group(1)
            p = re.compile('(' + '|'.join(config) + '):.+?cmsecs =\s+(\S+)\s')
            matches = re.findall(p, line)

            for i in range(len(config)):
                s = s + ' ' + get_data(config[i], matches)
            fw.write(s + '\n')
    fw.close()

    restore_dir()

def run(args):
    global log_dir

    if not args.run:
        return()

    if not args.device:
        error('Please designate device to run with')
        quit()

    backup_dir(src_dir)
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

    if args.run_nonroot:
        execute('platform_tools/android/bin/android_install_skia --release -s ' + args.device)
        if args.run_option:
            command = 'platform_tools/android/bin/android_run_skia --intent "bench --repeat 20 ' + args.run_option + '"'
        else:
            command = 'platform_tools/android/bin/android_run_skia --intent "bench --repeat 20"'
    else:
        execute('platform_tools/android/bin/android_install_skia --release --install-launcher -s ' + args.device)
        execute('platform_tools/android/bin/linux/adb shell stop')
        command = 'platform_tools/android/bin/android_run_skia bench --repeat 20'
        if args.run_option:
            command = command + ' ' + args.run_option

    group_log_dir = log_dir
    if args.run_times > 1:
        group_log_dir = log_dir + get_datetime() + '-' + args.device + '-bench/'
        os.mkdir(group_log_dir)

    for i in range(args.run_times):
        log_file = get_datetime() + '-' + args.device + '-bench-origin' + log_suffix
        command = command + ' 2>&1 |tee ' + group_log_dir + log_file
        start = datetime.datetime.now()
        execute(command)
        elapsed = (datetime.datetime.now() - start)
        info('Time elapsed to run: ' + str(elapsed.seconds) + 's')
        parse_result(group_log_dir, log_file)
        time.sleep(2)

    if not args.run_nonroot:
        execute('platform_tools/android/bin/linux/adb shell start')

    if args.run_times > 1:
        average(group_log_dir)

    restore_dir()

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


    backup_dir(src_dir)

    if build == 'Debug' or build == 'All':
        execute('platform_tools/android/bin/android_make -d ' + target + ' -j BUILDTYPE=Debug')

    if build == 'Release' or build == 'All':
        execute('platform_tools/android/bin/android_make -d ' + target + ' -j BUILDTYPE=Release')

    restore_dir()

def set_target(args):
    global target
    if not args.build and not args.run:
        return()

    target_from_option = ''
    if args.target == 'x86':
        target_from_option = 'x86'
    elif args.target == 's3':
        target_from_option = 'nexus4'
    elif args.target == 'nexus4':
        target_from_option = 'nexus_4'

    target_from_device = ''
    if args.device:
        # Guess target from 'adb devices -l'
        command = 'adb devices -l'
        devices = commands.getoutput(command).split('\n')

        for device in devices:
            if device[:len(args.device)] == args.device:
                if re.search('redhookbay', device):
                    target_from_device = 'x86'
                elif re.search('Medfield', device):
                    target_from_device = 'x86'
                elif re.search('mako', device):
                    target_from_device = 'nexus_4'
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

    backup_dir(root_dir)
    execute('gclient ' + args.update)
    restore_dir()

def setup(args):
    global root_dir
    global src_dir
    global platform_tools_dir
    global log_dir

    if args.root_dir:
        root_dir = args.root_dir
    else:
        root_dir = root_dir_default

    if not os.path.exists(root_dir):
        error('You must designate root_dir')
        quit()

    if args.log_dir:
        log_dir = args.log_dir
    else:
        log_dir = log_dir_default

    if not os.path.exists(log_dir):
        error('You must designate log_dir')
        quit()

    src_dir = root_dir + 'trunk/'
    platform_tools_dir = src_dir + 'platform_tools/'

    os.putenv('http_proxy', 'http://proxy-shz.intel.com:911')
    os.putenv('https_proxy', 'https://proxy-shz.intel.com:911')

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
  python %(prog)s -r release -d RHBEC245400171 // pr2
  python %(prog)s -r release --run-nonroot -d 006e7e464bd64fef --run-option '--match region_contains_sect --match verts'
  python %(prog)s -r release -d RHBEC245400171 --run-option '--match region_contains_sect --match verts'

  parse result:
  python %(prog)s --parse-result ORIGIN

  compare results:
  python %(prog)s -c BASE,COMPARED

  download:
  python %(prog)s --download nexus10

  average:
  python %(prog)s --average DIR

  update & build & run
  python %(prog)s -u sync -b release -r release -d RHBEC245400171
''')

    groupUpdate = parser.add_argument_group('update')
    groupUpdate.add_argument('-u', '--update', dest='update', help='gclient options to update source code')

    groupUpdate = parser.add_argument_group('build')
    groupUpdate.add_argument('-b', '--build', dest='build', help='type to build', choices=['release', 'debug', 'all'])

    groupUpdate = parser.add_argument_group('run')
    groupUpdate.add_argument('-r', '--run', dest='run', help='type to run', choices=['release', 'debug'])
    groupUpdate.add_argument('--run-nonroot', dest='run_nonroot', help='run without root access, which would not install skia_launcher to /system', action='store_true')
    groupUpdate.add_argument("--run-option", dest="run_option", help="option to run bench test", default='')
    groupUpdate.add_argument("--run-times", dest="run_times", help="times to run test", default=1, type=int)

    groupUpdate = parser.add_argument_group('parse result')
    groupUpdate.add_argument('--parse-result', dest='parse_result', help='log file to be parsed')

    groupUpdate = parser.add_argument_group('compare results')
    groupUpdate.add_argument('-c', '--compare', dest='compare', help='compare 2 formatted result files, format: BASE,COMPARED, the bigger the worse')

    groupUpdate = parser.add_argument_group('download')
    groupUpdate.add_argument('--download', dest='download', help='download result from Skia waterfall', choices=['nexus10', 'nexus4'])

    groupUpdate = parser.add_argument_group('average')
    groupUpdate.add_argument('--average', dest='average', help='calculate average of results within a directory')

    groupUpdate = parser.add_argument_group('other')
    groupUpdate.add_argument('-t', '--target', dest='target', help='target', choices=['x86', 's3', 'nexus4'])
    groupUpdate.add_argument('-d', '--device', dest='device', help='device id')
    groupUpdate.add_argument('--root-dir', dest='root_dir', help='root dir')
    groupUpdate.add_argument('--log-dir', dest='log_dir', help='log dir')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()

    setup(args)
    update(args)
    set_target(args)
    build(args)
    run(args)

    if args.parse_result:
        parse_result(log_dir, args.parse_result)

    compare(args)
    download(args)

    if args.average:
        average(args.average)