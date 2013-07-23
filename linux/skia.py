#! N:\Python27\python.exe
# -*- coding: utf-8 -*-

# Usage:
# python skia.py -r 2 -o '--match region_contains_sect --match verts'

import re
from optparse import OptionParser
import os
import datetime

log_dir = '/workspace/topic/skia/log'
log_suffix = '.txt'
config = ['8888', '565', 'GPU', 'NULLGPU']
NA = 'NA'

def info(msg):
    print "[INFO] " + msg + "."

def error(msg):
    print "[ERROR] " + msg + "!"

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
    return now.strftime("%Y%m%d%H%M%S%f")

def parse_result(file):
    fr = open(log_dir + '/' + file + log_suffix)
    lines = fr.readlines()
    fr.close();
    
    fw = open(log_dir + '/' + file + '_format' + log_suffix, 'w')
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

def run_test(options):
    format_files = ''
    repeat = int(options.bench_repeat)
    
    os.chdir('/workspace/project/android/skia/trunk')
    #os.system('../android/bin/android_install_skia --release --install-launcher -s Medfield6CCF763B') # pr2
    #os.system('../android/bin/android_install_skia --release --install-launcher -s Medfield0C9F03BE') # xt890
    os.system('../android/bin/linux/adb shell stop')

    for i in range(repeat):
        f = get_datetime() + '_CTP_bench'

        cmd = '../android/bin/android_run_skia bench --repeat 20'
        if options.bench_option:
            cmd = cmd + ' ' + options.bench_option
        cmd = cmd + ' 2>&1 |tee '+ log_dir + '/' + f + '.txt'
        
        print cmd
        os.system(cmd)
        parse_result(f)
        if format_files != '':
            format_files = format_files + ','
        format_files = format_files + f + '_format' + log_suffix
        
    os.system('../android/bin/linux/adb shell start')
    if repeat > 1:
        compare_result(format_files)

def parse_format_result(file, base):
    fr = open(log_dir + '/' + file)
    lines = fr.readlines()
    fr.close()    

    for line in lines:
        if re.match('^\s+$', line):
            continue
        p = re.compile('\S+')
        base.append(re.findall(p, line))

def compare_result(files):
    f = files.split(',')
    
    file_number = len(f)
    base = []
    total = []
    parse_format_result(f[0], base)
    parse_format_result(f[0], total)

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

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-r", "--bench-repeat", dest="bench_repeat", help="Times to run bench test", default=0)
    parser.add_option("-o", "--bench-option", dest="bench_option", help="Option to run bench test", default='')
    parser.add_option("-p", "--parse-result", dest="parse_result", help="Parse result file", default='')
    parser.add_option("-c", "--compare-result", dest="compare_result", help="Compare result file", default='')
    (options, args) = parser.parse_args()
    
    if options.bench_repeat:
        run_test(options)

    if options.parse_result:
        parse_result(options.parse_result)
    
    if options.compare_result:
        compare_result(options.compare_result)
