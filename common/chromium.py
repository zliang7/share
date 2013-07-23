#/usr/bin/python

import os
import commands
import argparse
import platform
import re
import sys

# Global variables
root_dir = ''
src_dir = ''
system = platform.system()

def is_system(name):
    if system == name:
        return True
    else:
        return False

def is_windows():
    if is_system('Windows'):
        return True
    else:
        return False

def is_linux():
    if is_system('Linux'):
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

def has_build_dir(name):
    out_dir = src_dir + '/out'
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    build_dir = out_dir + '/' + name
    if not os.path.exists(build_dir):
        warning(name + ' directory doesn\'t exist. Will create the directory for you and perform a clean build')
        os.mkdir(build_dir)
        return False

    return True

def update(args):
    if not args.update:
        return()

    # 'third_party/skia/src' is not on master
    repos = ['./', 'third_party/WebKit']
    for repo in repos:
        is_master = False
        os.chdir(src_dir + '/' + repo)
        branches = commands.getoutput('git branch').split('\n')
        for branch in branches:
            if branch == '* master':
                is_master = True

        if not is_master:
            error('Repo ' + repo + ' is not on master')
            quit()

    os.chdir(root_dir)
    if is_windows():
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

    build_clean = args.build_clean
    if build == 'All':
        if not has_build_dir('Debug') and not has_build_dir('Release'):
            build_clean = True
    else:
        if not has_build_dir(build):
            build_clean = True

    print '== Build Environment =='
    print 'Directory of src: ' + src_dir
    print 'Build type: ' + build
    print 'Build system: Ninja'
    print 'Need clean build: ' + str(build_clean)
    print 'System: ' + system
    print '======================='

    os.chdir(src_dir)

    if build_clean:
        cmd = 'python build/gyp_chromium'
        execute(cmd)

    if args.build_verbose:
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

    option = '--disable-setuid-sandbox --disable-hang-monitor --allow-file-access-from-files --user-data-dir=' + root_dir + '/user-data'
    if args.run_option:
        option = option + ' ' + args.run_option

    if args.run_GPU:
        option = option + ' ' + '--enable-accelerated-2d-canvas --ignore-gpu-blacklist'

    if args.run_debug_renderer:
        if args.run.upper() == 'RELEASE':
            warning('Debugger should run with debug version. Switch to it automatically')
            args.run = 'debug'
        option = option + ' ' + '--renderer-cmd-prefix="xterm -title renderer -e gdb --args"'

    cmd = root_dir + '/src/out/' + args.run.capitalize() + '/chrome ' + option
    execute(cmd)

def find_owner(args):
    if not args.owner:
        return()

    os.chdir(src_dir)
    files = commands.getoutput('git diff --name-only HEAD origin/master').split('\n')
    owner_file_map = {} # map from OWNERS file to list of modified files
    for file in files:
        dir = os.path.dirname(file)
        while not os.path.exists(dir + '/OWNERS'):
            dir = os.path.dirname(dir)

        owner_file = dir + '/OWNERS'
        if owner_file in owner_file_map:
            owner_file_map[owner_file].append(file)
        else:
            owner_file_map[owner_file] = [file]

    for owner_file in owner_file_map:
        owner = commands.getoutput('cat ' + dir + '/OWNERS')
        print '--------------------------------------------------'
        print '[Modified Files]'
        for modified_file in owner_file_map[owner_file]:
            print modified_file
        print '[OWNERS File]'
        print owner


# override format_epilog to make it format better
argparse.format_epilog = lambda self, formatter: self.epilog

if __name__ == '__main__':
    # System sanity check
    if not is_windows() and not is_linux():
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

  python %(prog)s --owner

  update & build & run
  python chromium.py -u sync -b release -r release
''')

    groupUpdate = parser.add_argument_group('update')
    groupUpdate.add_argument('-u', '--update', dest='update', help='gclient options to update source code')

    groupBuild = parser.add_argument_group('build')
    groupBuild.add_argument('-b', '--build', dest='build', help='type to build', choices=['release', 'debug', 'all'])
    groupBuild.add_argument('-c', '--build-clean', dest='build_clean', help='regenerate gyp', action='store_true')
    groupBuild.add_argument('-v', '--build-verbose', dest='build_verbose', help='output verbose info. Find log at out/Release/.ninja_log', action='store_true')

    groupRun = parser.add_argument_group('run')
    groupRun.add_argument('-r', '--run', dest='run', help='type to run', choices=['release', 'debug'])
    groupRun.add_argument('-o', '--run-option', dest='run_option', help='option to run')
    groupRun.add_argument('-g', '--run-gpu', dest='run_GPU', help='enable GPU acceleration', action='store_true')
    groupRun.add_argument('--run-debug-renderer', dest='run_debug_renderer', help='run gdb before renderer starts', action='store_true')

    # Other options
    parser.add_argument('--owner', dest='owner', help='find owner for latest commit', action='store_true')
    parser.add_argument('-d', '--root-dir', dest='root_dir', help='set root directory')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()

    # Global variables
    if not args.root_dir:
        if is_windows():
            root_dir = "d:/user/ygu5/project/chromium"
        else:
            root_dir = '/workspace/project/chromium'
    else:
        root_dir = args.root_dir

    src_dir = root_dir + '/src'

    os.putenv('http_proxy', 'http://proxy-shz.intel.com:911')
    os.putenv('https_proxy', 'https://proxy-shz.intel.com:911')

    if is_windows():
        path = os.getenv('PATH')
        p = re.compile('depot_tools')
        if not p.search(path):
            path = 'd:\user\ygu5\project\chromium\depot_tools;' + path
            os.putenv('PATH', path)

    os.putenv('GYP_GENERATORS', 'ninja')
    if is_windows():
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
    find_owner(args)
