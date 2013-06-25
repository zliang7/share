#/usr/bin/python

import os
import commands
from optparse import OptionParser
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
    print "[INFO] " + msg + "."

def error(msg):
    print "[ERROR] " + msg + "!"

def hasBuildDir(name):
    outDir = srcDir + '/out'
    if not os.path.exists(outDir):
        os.mkdir(outDir)

    buildDir = outDir + '/' + name
    if not os.path.exists(buildDir):
        info(name + " directory doesn't exist. Will create the directory for you and perform a clean build")
        os.mkdir(buildDir)
        return False

    return True

def gclient(options):
    if options.gclient == '':
        return()

    os.chdir(rootDir)
    if isWindows():
        cmd = 'd:/user/ygu5/project/chromium/depot_tools/gclient'
    else:
        cmd = 'gclient'
        
    cmd = cmd + ' ' + options.gclient    
    info(cmd)
    print os.system(cmd)
    
def build(options):   
    if options.buildType == '':
        return()
    
    if options.buildType.upper() == "DEBUG":
        buildType = "Debug"
    elif options.buildType.upper() == "RELEASE":
        buildType = "Release"
    elif options.buildType.upper() == "ALL":
        buildType = "All"

    cleanBuild = options.cleanBuild    
    if buildType == "All":
        if not hasBuildDir("Debug") and not hasBuildDir("Release"):
            cleanBuild = True
    else:
        if not hasBuildDir(buildType):
            cleanBuild = True
    
    print "== Build Environment =="
    print "Directory of src: " + srcDir
    print "Build type: " + buildType
    print "Build system: Ninja"
    print "Need clean build: " + str(cleanBuild)
    print "System: " + system
    print "======================="
        
    os.chdir(srcDir)
        
    if cleanBuild:
        cmd = 'python build/gyp_chromium'
        os.system(cmd)
    
    if options.verbose:
        cmd = 'ninja -v chrome'
    else:
        cmd = 'ninja chrome'

    if buildType == "Debug" or buildType == "All":
        cmd = cmd + ' -C out/Debug'
        print cmd
        os.system(cmd)

    if buildType == "Release" or buildType == "All":
        cmd = cmd + ' -C out/Release'
        os.system(cmd)
    
# override format_epilog to make it format better
OptionParser.format_epilog = lambda self, formatter: self.epilog

if __name__ == "__main__":
    # System sanity check
    if not isWindows() and not isLinux():
        error('Current system is not suppported')
        quit()
        
    # Handle options
    parser = OptionParser(description='Description: Script to sync and build Chromium',
                          epilog="""
Examples:
  python chromium_build.py -g "sync"
  python chromium_build.py -g "sync --force"
  python chromium_build.py -g "runhooks"
  python chromium_build.py -t release
""")
    parser.add_option("-g", "--gclient", dest="gclient", help="Update source code", default='')
    parser.add_option("-c", "--clean-build", action="store_true", dest="cleanBuild", help="need a clean build", default=False)
    parser.add_option("-t", "--build-type", dest="buildType", help="assign the build type", metavar="DEBUG|RELEASE|ALL", default='')
    parser.add_option("-d", "--root-dir", dest="rootDir", help="assign root directory of Chromium", metavar="ROOTDIR", default='')
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="enable verbose mode for ninja. Find log at out/Release/.ninja_log", default=False)
    (options, args) = parser.parse_args()

    # Global variables
    if options.rootDir == '':
        if isWindows():
            rootDir = "d:/user/ygu5/project/chromium"
        else:
            rootDir = "/workspace/project/chromium"
    else:
        rootDir = options.rootDir
        
    srcDir = rootDir + '/src'

    os.putenv('http_proxy', 'http://proxy-shz.intel.com:911')
    os.putenv('https_proxy', 'https://proxy-shz.intel.com:911')
    
    if isWindows():
        path = os.getenv("PATH")
        p = re.compile('depot_tools')
        if not p.search(path):
            path = "d:\user\ygu5\project\chromium\depot_tools;" + path
            os.putenv("PATH", path)        
    
    os.putenv("GYP_GENERATORS", "ninja")
    if isWindows():
        os.putenv('GYP_DEFINES', 'werror= disable_nacl=1 component=shared_library enable_svg=0 windows_sdk_path="d:/user/ygu5/project/chromium/win_toolchain/win8sdk"')
        os.putenv("GYP_MSVS_VERSION", "2010e")
        os.putenv("GYP_MSVS_OVERRIDE_PATH", "d:/user/ygu5/project/chromium/win_toolchain")
        os.putenv("WDK_DIR", "d:/user/ygu5/project/chromium/win_toolchain/WDK")
        os.putenv("DXSDK_DIR", "d:/user/ygu5/project/chromium/win_toolchain/DXSDK")
        os.putenv("WindowsSDKDir", "d:/user/ygu5/project/chromium/win_toolchain/win8sdk")
    else:
        os.putenv("GYP_DEFINES", "werror= disable_nacl=1 component=shared_library enable_svg=0")    
    
    # Real work
    gclient(options)
    build(options)
    
