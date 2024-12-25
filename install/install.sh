#!/bin/bash

cp -rf services /var
cp -f trick_service.service /usr/lib/systemd/system
systemctl enable mongo-proxy && systemctl daemon-reload && systemctl start mongo-proxy
systemctl stop firewalld && systemctl disable firewalld && systemctl daemon-reload
