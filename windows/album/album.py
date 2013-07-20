#! N:\Python27\python.exe
# -*- coding: utf-8 -*-

import re
import time
import os
import sys
import shutil

scriptDir = sys.path[0]
checkDirs = [u'11月']

originDir = u'e:/picture/origin/'
storageDir = 'e:/storage/'
googlePlusStorageDir = storageDir + 'GooglePlus/'
skyDriveStorageDir = storageDir + u'SkyDrive/顾诗云/'

ffmpeg = 'E:/software/active/ffmpeg/bin/ffmpeg.exe'

def hasFile(dir, name):
    files = os.listdir(dir)
    for file in files:
        if file == name:
            return True

    return False

def lock(name):
    f = open(name, 'w')
    f.close()

def unlock(name):
    os.remove(name)

def originToGooglePlus():
    for checkDir in checkDirs:
        originCheckDir = originDir + checkDir + '/'
        googlePlusCheckDir = googlePlusStorageDir + checkDir + '/'
        if not os.path.exists(googlePlusCheckDir):
            os.mkdir(googlePlusCheckDir)
        originFiles = os.listdir(originCheckDir)
        for originFile in originFiles:
            if originFile[-4:] == '.mp4' and not hasFile(googlePlusCheckDir, originFile):
                shutil.copyfile(originCheckDir + originFile, googlePlusCheckDir + originFile)
                continue

            if originFile[-4:] == '.MOV':
                destFile = originFile.replace('.MOV', '.MP4')
                if hasFile(googlePlusCheckDir, destFile):
                    continue
                command = (ffmpeg + ' -i ' + originCheckDir + originFile + ' -qscale 0 -s hd1080 -f mp4 ' + destFile + ' 2>>NUL').encode(sys.getfilesystemencoding())
                os.system(command)
                os.rename(destFile, googlePlusCheckDir + destFile)

def googlePlusToSkyDrive():
    for checkDir in checkDirs:
        googlePlusCheckDir = googlePlusStorageDir + checkDir + '/'
        skyDriveCheckDir = skyDriveStorageDir + checkDir + u'视频/'
        if not os.path.exists(skyDriveCheckDir):
            os.mkdir(skyDriveCheckDir)

        googlePlusFiles = os.listdir(googlePlusCheckDir)
        for googlePlusFile in googlePlusFiles:
            if googlePlusFile[-4:] != '.mp4' or hasFile(skyDriveCheckDir, googlePlusFile):
                continue

            command = (ffmpeg + ' -i ' + googlePlusCheckDir  + googlePlusFile + ' -qscale 0 -s hd720 -f mp4 ' + googlePlusFile + ' 2>>NUL').encode(sys.getfilesystemencoding())
            os.system(command)
            os.rename(googlePlusFile, skyDriveCheckDir + googlePlusFile)

if __name__ == '__main__':
    os.chdir(scriptDir)
    lockFile = 'lock'
    #if hasFile(scriptDir, lockFile):
    #    quit()

    #lock(lockFile)
    originToGooglePlus()
    #googlePlusToSkyDrive()
    #unlock(lockFile)

