#!/bin/bash

# add to path
PATH=$PATH:/project/joshuaelliott/1896/utils

swift -sites.file midway.xml -tc.file tc.data dbf2nc.swift

# Remove run directories if Swift finishes with no errors
if [ $? -eq 0 ]; then
   echo Removing run directory . . .
   rm -rf run???
fi
