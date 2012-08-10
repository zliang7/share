SHARE_LINUX_DIR=$1
if [ !SHARE_DIR ]; then
    SHARE_LINUX_DIR=/workspace/project/gyagp/share/linux
fi


cp $SHARE_LINUX_DIR/.bashrc ~/
cp $SHARE_LINUX_DIR/.gdbinit ~/
cp $SHARE_LINUX_DIR/.gitconfig ~/
cp $SHARE_LINUX_DIR/


# before installation
# backup desktope
# backup chrome opened tab

# install visual slick edit
# install zsh
# install git
