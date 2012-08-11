#/usr/bin/python

# Description:
# This file would help to set up environment after fresh building of a new Ubuntu system.
#
# Pre-installation: 
# Backup files in desktop, opened tab in Chrome.
#
# Post-installation: 
# Install display card driver, slickedit.
# Run /workspace/project/chromium/git_upstream/src/build/install-build-deps.sh. This file would help to install many development tools.

import os;
import commands;
import re;

srcDir = "/workspace/project/gyagp/share/linux";
homeDir = os.getenv("HOME");
user = os.getenv("USER");

def info(msg):
    print "[INFO] " + msg + ".";

def error(msg):
    print "[ERROR] " + msg + "!";

def patchSudo():
    sudoFile = "10_gyagp_sudo";
    (status, output) = commands.getstatusoutput("timeout 1s sudo cat /etc/sudoers.d/" + sudoFile);
    if status != 0:
        status = copyFile(sudoFile, "/etc/sudoers.d", 1);
        if status == 0:
            info("Now you can sudo without password");
            # No need to run following command to take effect
            #commands.getstatusoutput("/etc/init.d/sudo restart"); 
    else:
        info("You were able to sudo without password");

def copyFile(srcFile, destDir, sudo, srcSubDir = ""):
    if cmp(srcSubDir, "") == 1:
        srcPath = srcDir + "/" + srcSubDir + "/" + srcFile;
    else:
        srcPath = srcDir + "/" + srcFile;

    if not os.path.exists(srcPath):
        error(srcPath + " doesn't exist");
        return -1;

    if os.path.exists(destDir + "/" + srcFile):
        info(destDir + "/" + srcFile + " already exists");
        return 0;
    
    if not os.path.exists(destDir):
        commands.getstatusoutput("mkdir -p " + destDir);
        info(srcFile + destDir + " doesn't exist, so just create it");


    command = "cp " + srcPath + " " + destDir;
    if sudo:
        command = "sudo " + command;
    
    (status, output) = commands.getstatusoutput(command);
    return status;

def overwriteFile(srcFile, destDir, sudo, srcSubDir = ""):
    if not os.path.exists(destDir + "/" + srcFile):
        error(destDir + "/" + srcFile + " doesn't exist");
        return -1;

    if os.path.exists(destDir + "/" + srcFile + ".bk"):
        info(destDir + "/" + srcFile + " was already overwritten");
        return 0;

    command = "mv " + destDir + "/" + srcFile + " " + destDir + "/" + srcFile + ".bk";
    if sudo:
        command = "sudo " + command;

    (status, output) = commands.getstatusoutput(command);

    status = copyFile(srcFile, destDir, sudo, srcSubDir);
    if status == 0:
        info(srcFile + " has replaced the original file successfully");
    else:
        error(srcFile + " didn't replace the original file successfully");

    return status;

def installPackage(pkg):
    (status, output) = commands.getstatusoutput("dpkg -s " + pkg);
    if status != 0:
        info("Package " + pkg + " is installing...");
        (status, output) = commands.getstatusoutput("sudo apt-get install -y " + pkg);
        if status != 0:
            error("Package " + pkg + "'s installation failed");
            return -1;
        else:
            return 0;

    else:
        info("Package " + pkg + " was already installed");    
        return -1;

if __name__ == "__main__":
    patchSudo();

    installPackage("tsocks");
    overwriteFile("tsocks.conf", "/etc", 1);

    (status, output) = commands.getstatusoutput("cat /etc/apt/sources.list |grep 'ubuntu.com'");
    if status == 0: # need overwrite
        (status, output) = commands.getstatusoutput("awk '{print $2}' /etc/issue");
        output = output[:-1];
        status = overwriteFile("sources.list", "/etc/apt", 1, "apt/" + output);
        if status == 0:
            os.system("sudo apt-get update");
    else:
        info("/etc/apt/sources.list was already updated"); 

    # Need to use tsocks
    (status, output) = commands.getstatusoutput("sudo apt-key list | grep 7FAC5991");
    if status:
        info("Get the key for Chrome...");
        (status, output) = commands.getstatusoutput("tsocks wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -");   
        if status != 0:
            error("Key for Chrome hasn't been added correctly");
    else:
        info("Key for Chrome has been added");


    copyFile("apt.conf", "/etc/apt", 1);
    copyFile("gyagp.list", "/etc/apt/sources.list.d", 1);    
    
    installPackage("gparted");

    
    status = installPackage("zsh");
    if status == 0:
        copyFile(".zshrc", homeDir, 0);
        # use sudo to bypass password input
        commands.getstatusoutput("sudo chsh -s /bin/zsh " + user);

    installPackage("gnome-shell");
    installPackage("vim");
    
    installPackage("git");
    copyFile("connect", "/usr/bin", 1);
    copyFile("socks-gw", "/usr/bin", 1);
    copyFile("git.sh", "/etc/profile.d", 1);
    copyFile(".gitconfig", homeDir, 0);

    installPackage("ssh");
    
    copyFile(".bashrc", homeDir, 0);
    
    copyFile(".gdbinit", homeDir, 0);
    
    copyFile("gyagp.sh", "/etc/profile.d", 1);
    
    installPackage("ssh");
    installPackage("gnome-shell");
    installPackage("most");

    installPackage("binutils-gold");

    copyFile("include.gypi", homeDir + "/.gyp", 0);

    installPackage("google-chrome-unstable");
    
    installPackage("vnc4server");
    
    status = installPackage("apt-file");
    if status == 0:
        commands.getstatusoutput("sudo apt-file update");



    # post installation
    # Run vncserver to start vnc server
