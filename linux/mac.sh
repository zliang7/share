sudo ifconfig wlan0 down
sudo ifconfig wlan0 hw ether 02:87:f8:f6:e6:e6
sudo ifconfig wlan0 up
sudo /etc/init.d/networking restart
