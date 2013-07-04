#/usr/bin/python

import os
import commands
import argparse
import platform
import re

# Global variables
rootDir = ''
srcDir = ''
system = platform.system()

def isSystem(name):
    if system == name:
        return True
    else:
        return False
        
def isWindows():
    if isSystem('Windows'):
        return True
    else:
        return False

def isLinux():
    if isSystem('Linux'):
        return True
    else:
        return False
        
def info(msg):
    print '[INFO] ' + msg + '.'

def warning(msg):
    print '[WARNING] ' + msg + '.'

def error(msg):
    print '[ERROR] ' + msg + '!'

def cmd(msg):
    print '[COMMAND] ' + msg
    
def execute(command):
    cmd(command)
    if os.system(command):
        error('Failed to execute')
        quit()

def hasBuildDir(name):
    outDir = srcDir + '/out'
    if not os.path.exists(outDir):
        os.mkdir(outDir)

    buildDir = outDir + '/' + name
    if not os.path.exists(buildDir):
        warning(name + ' directory doesn\'t exist. Will create the directory for you and perform a clean build')
        os.mkdir(buildDir)
        return False

    return True

def update(args):
    if not args.update:
        return()

    os.chdir(rootDir)
    if isWindows():
        cmd = 'd:/user/ygu5/project/chromium/depot_tools/gclient'
    else:
        cmd = 'gclient'
        
    cmd = cmd + ' ' + args.update
    execute(cmd)
    
    
def build(args):   
    if not args.build:
        return()
    
    if args.build.upper() == 'DEBUG':
        build = 'Debug'
    elif args.build.upper() == 'RELEASE':
        build = 'Release'
    elif args.build.upper() == 'ALL':
        build = 'All'

    buildClean = args.buildClean
    if build == 'All':
        if not hasBuildDir('Debug') and not hasBuildDir('Release'):
            buildClean = True
    else:
        if not hasBuildDir(build):
            buildClean = True
    
    print '== Build Environment =='
    print 'Directory of src: ' + srcDir
    print 'Build type: ' + build
    print 'Build system: Ninja'
    print 'Need clean build: ' + str(buildClean)
    print 'System: ' + system
    print '======================='
        
    os.chdir(srcDir)
        
    if buildClean:
        cmd = 'python build/gyp_chromium'
        execute(cmd)
    
    if args.buildVerbose:
        cmd = 'ninja -v chrome'
    else:
        cmd = 'ninja chrome'

    if build == 'Debug' or build == 'All':
        execute(cmd + ' -C out/Debug')

    if build == 'Release' or build == 'All':
        execute(cmd + ' -C out/Release')

def run(args):
    if not args.run:
        return()

    option = '--disable-setuid-sandbox --disable-hang-monitor --allow-file-access-from-files --user-data-dir=' + rootDir + '/user-data'
    if args.runOption:
        option = option + ' ' + args.runOption
        
    if args.runGPU:
        option = option + ' ' + '--enable-accelerated-2d-canvas --ignore-gpu-blacklist'

    if args.runDebugRenderer:
        if args.run.upper() == 'RELEASE':
            warning('Debugger should run with debug version. Switch to it automatically')
            args.run = 'debug'
        option = option + ' ' + '--renderer-cmd-prefix="xterm -title renderer -e gdb --args"'
    
    cmd = rootDir + '/src/out/' + args.run.capitalize() + '/chrome ' + option
    execute(cmd)
    
# override format_epilog to make it format better
argparse.format_epilog = lambda self, formatter: self.epilog

if __name__ == '__main__':
    # System sanity check
    if not isWindows() and not isLinux():
        error('Current system is not suppported')
        quit()
        
    # Handle options
    parser = argparse.ArgumentParser(description = 'Script to update, build and run Chromium',
                                     formatter_class = argparse.RawTextHelpFormatter,
                                     epilog = '''
examples:

  update:
  python %(prog)s -u sync
  python %(prog)s -u 'sync --force'
  python %(prog)s -u runhooks
  
  build:
  python %(prog)s -b release
  python %(prog)s -b all
  python %(prog)s -b release -c -v
  
  run:
  python %(prog)s -r release
  python %(prog)s -r release -g
  python %(prog)s -r debug
  python %(prog)s -r release -o=--enable-logging=stderr
  python %(prog)s -r release -o--enable-logging=stderr
  python %(prog)s -r release '-o --enable-logging=stderr'
  python %(prog)s -r release --run-debug-renderer
  
  update & build & run
  python chromium.py -u sync -b release -r release
''')

    groupUpdate = parser.add_argument_group('update')
    groupUpdate.add_argument('-u', '--update', dest='update', help='gclient options to update source code')

    groupBuild = parser.add_argument_group('build')
    groupBuild.add_argument('-b', '--build', dest='build', help='type to build', choices=['release', 'debug', 'all'])
    groupBuild.add_argument('-c', '--build-clean', dest='buildClean', help='regenerate gyp', action='store_true')
    groupBuild.add_argument('-v', '--build-verbose', dest='buildVerbose', help='output verbose info. Find log at out/Release/.ninja_log', action='store_true')

    groupRun = parser.add_argument_group('run')
    groupRun.add_argument('-r', '--run', dest='run', help='type to run', choices=['release', 'debug'])
    groupRun.add_argument('-o', '--run-option', dest='runOption', help='option to run')
    groupRun.add_argument('-g', '--run-gpu', dest='runGPU', help='enable GPU acceleration', action='store_true')
    groupRun.add_argument('--run-debug-renderer', dest='runDebugRenderer', help='run gdb before renderer starts', action='store_true')

    # Other options
    parser.add_argument('-d', '--root-dir', dest='rootDir', help='set root directory')
    
    args = parser.parse_args()

    if not (args.update or args.build or args.run):
        parser.print_help()

    # Global variables
    if not args.rootDir:
        if isWindows():
            rootDir = "d:/user/ygu5/project/chromium"
        else:
            rootDir = '/workspace/project/chromium'
    else:
        rootDir = args.rootDir
        
    srcDir = rootDir + '/src'

    os.putenv('http_proxy', 'http://proxy-shz.intel.com:911')
    os.putenv('https_proxy', 'https://proxy-shz.intel.com:911')
    
    if isWindows():
        path = os.getenv('PATH')
        p = re.compile('depot_tools')
        if not p.search(path):
            path = 'd:\user\ygu5\project\chromium\depot_tools;' + path
            os.putenv('PATH', path)        
    
    os.putenv('GYP_GENERATORS', 'ninja')
    if isWindows():
        os.putenv('GYP_DEFINES', 'werror= disable_nacl=1 component=shared_library enable_svg=0 windows_sdk_path="d:/user/ygu5/project/chromium/win_toolchain/win8sdk"')
        os.putenv('GYP_MSVS_VERSION', '2010e')
        os.putenv('GYP_MSVS_OVERRIDE_PATH', 'd:/user/ygu5/project/chromium/win_toolchain')
        os.putenv('WDK_DIR', 'd:/user/ygu5/project/chromium/win_toolchain/WDK')
        os.putenv('DXSDK_DIR', 'd:/user/ygu5/project/chromium/win_toolchain/DXSDK')
        os.putenv('WindowsSDKDir', 'd:/user/ygu5/project/chromium/win_toolchain/win8sdk')
    else:
        os.putenv('GYP_DEFINES', 'werror= disable_nacl=1 component=shared_library enable_svg=0')
        os.putenv('CHROME_DEVEL_SANDBOX', '/usr/local/sbin/chrome-devel-sandbox')
    
    # Real work
    update(args)
    build(args)
    run(args)
    
