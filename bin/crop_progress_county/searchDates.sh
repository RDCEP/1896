#!/bin/bash

for dir in CPdata/CP_data_files-2013/*; do
    if [ $dir != CPdata/CP_data_files-2013/zips ] && [ "$(ls -A $dir)" ]; then
        nf=$(ls $dir | wc -l)
        cnt=0
        for f in $dir/*; do
            a=$(cat $f | grep ${dir:26})
            if [ "$a" != "" ]; then
                cnt=$((cnt+1))
            else
                echo "$f doesn't match"
            fi
        done
        echo $nf, $cnt
    fi
done

# for dir in CPdata/CP_data_files-2011/*; do
#     if [ "$(ls -A $dir/temp)" ]; then
#         nf=$(ls $dir/temp | wc -l)
#         cnt=0
#         for f in $dir/temp/*; do
#             a=$(cat $f | grep 2011${dir:28:4})
#             if [ "$a" != "" ]; then
#                 cnt=$((cnt+1))
#             else
#                 echo "$f doesn't match"
#             fi
#         done
#         echo $nf, $cnt
#     fi
# done