#! N:\Python27\python.exe
# -*- coding: utf-8 -*-

import re
import os
import datetime
import argparse
import platform
import sys
import commands

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

SMALL_NUMBER = 0.000001
LARGE_NUMBER = 10000

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

def download(args):
    if not args.download:
        return()

    if args.download != 'nexus_10':
        error('Only Nexus 10 is supported now')
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
    if args.download == 'nexus_10':
        link = 'Nexus10-MaliT604-Arm7'
    origin_file = log_dir + link + '-' + str(build_number) + '-bench-origin' + log_suffix

    if os.path.exists(origin_file):
        info(origin_file + ' has been downloaded')
        return()

    url = 'http://108.170.217.252:10117/builders/Perf-Android-' + link + '-Release/builds/' + build_number + '/steps/RunBench/logs/stdio/text'
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



def _parse_format_result(log_file, results):
    os.chdir(log_dir)
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
    total = []
    _parse_format_result(files[0], base)
    _parse_format_result(files[0], total)

    for i in range(1, file_number):
        compared = []
        _parse_format_result(files[i], compared)

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
                        total[base_index][j] = NA
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
                        total[base_index][j] = float(total[base_index][j]) + c
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

    # Don't calculate average for the time being
    return()
    # Print average
    info('== Average ==')
    for i in range(len(total)):
        s = ''
        for j in range(1, len(total[i])):
            if total[i][j] == NA:
                s = s + ' NA'
            else:
                s = s + ' ' + ('%.2f' %(float(total[i][j]) / file_number))
        s = total[i][0] + s
        print s


def parse_result(log_file):
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


    log_file = log_dir + get_datetime() + '-' + args.device + '-bench-origin' + log_suffix
    command = command + ' 2>&1 |tee '+  log_file

    start = datetime.datetime.now()
    execute(command)
    elapsed = (datetime.datetime.now() - start)
    info('Time elapsed to run: ' + str(elapsed.seconds) + 's')

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
    elif args.target == 'nexus_4':
        target_from_option = 'nexus_4'

    target_from_device = ''
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

    os.chdir(root_dir)
    execute('gclient ' + args.update)

def setup(args):
    global root_dir
    global src_dir
    global platform_tools_dir
    global log_dir

    if args.root_dir:
        root_dir = args.root_dir
    else:
        root_dir = '/workspace/project/skia/'

    if not os.path.exists(root_dir):
        error('You must designate root_dir')
        quit()

    if args.log_dir:
        log_dir = args.log_dir
    else:
        log_dir = '/workspace/topic/skia/log/'

    if not os.path.exists(log_dir):
        error('You must designate log_dir')
        quit()

    src_dir = root_dir + 'trunk/'
    platform_tools_dir = src_dir + 'platform_tools/'

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
  python %(prog)s -r release --run-nonroot -d 32300bd273508f3b --bench-option '--match region_contains_sect --match verts'
  python %(prog)s -r release -d RHBEC245400171 --bench-option '--match region_contains_sect --match verts'

  parse result:
  python %(prog)s --parse-result /workspace/topic/skia/log/20130725173815-RHBEC245400171-bench-origin.txt

  compare results:
  python %(prog)s -c Nexus10-MaliT604-Arm7-416-bench-format.txt,20130726183834_006e7e464bd64fef_bench_format.txt

  download:
  python %(prog)s --download nexus_10

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

    groupUpdate = parser.add_argument_group('parse result')
    groupUpdate.add_argument('--parse-result', dest='parse_result', help='log file to be parsed')

    groupUpdate = parser.add_argument_group('compare results')
    groupUpdate.add_argument('-c', '--compare', dest='compare', help='compare 2 formatted result files, format: BASE,COMPARED, the bigger the worse')

    groupUpdate = parser.add_argument_group('download')
    groupUpdate.add_argument('--download', dest='download', help='download result from Skia waterfall', choices=['nexus_10'])

    groupUpdate = parser.add_argument_group('other')
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
        parse_result(args.parse_result)

    compare(args)

    download(args)