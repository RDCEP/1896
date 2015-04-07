#!/bin/bash

PATH=$PATH:/project/joshuaelliott/1896/src/crop_progress_county

swift -sites.file midway.xml -tc.file tc.data combineDBF.swift

# Remove run directories if Swift finishes with no errors
if [ $? -eq 0 ]; then
   echo Removing run directory . . .
   rm -rf run???
fi
