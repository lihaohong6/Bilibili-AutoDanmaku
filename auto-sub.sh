CONFIG_FILE=./config.sh

. "$CONFIG_FILE"

# DANMAKU_FILE=./danmaku.xml
# DANMAKU_ASS=./danmaku.ass
# PYTHON_SCRIPT=./danmaku2ass.py
# FLV_LIST=./flv_files.txt
# MERGED_FILE=./merged.flv
# VIDEO_WITH_DANMAKU=./final.flv

function assert_file_exist {
	if [ ! -f "$1" ]; then
		echo "no file named $1 present"
		if [ $# -eq 2 ]; then
			echo "$2"
		fi
		exit 1
	fi
}

function execute_if_not_exist {
	FILE_NAME=$1
	FUNCTION_NAME=$2
	if [ ! -f "$FILE_NAME" ]; then
		$FUNCTION_NAME
	fi
	assert_file_exist "$FILE_NAME"
}

function convert_xml_to_ass() {
	# try to find ass file; if not exist, convert the xml file to ass
	assert_file_exist "$DANMAKU_FILE"
	echo "XML danmaku file found, now converting"
	assert_file_exist "$PYTHON_SCRIPT"
	echo "converting from xml to ass"
	python "$PYTHON_SCRIPT" -o "$DANMAKU_ASS" -s 1920x1080 -f Bilibili -fn "Microsoft Yahei" "$DANMAKU_FILE"
}

function merge_videos {
	# find all flv files and put their names in a txt file
	rm -f "$FLV_LIST"
	LAST_FILE=PLACE_HOLDER
	for FILE in ./*; do
	    if [[ "$FILE" == *.flv ]]; then
	        printf "file '$FILE'\n" >> "$FLV_LIST" 
	        LAST_FILE="$FILE"
	    fi
	done;
	assert_file_exist "$FLV_LIST" "You need as least 1 file with the extension .flv"

	# count the number of flv files
	FILE_COUNT=$(wc -l "$FLV_LIST" | awk '{print $1}')
	echo "$FILE_COUNT flv files found"

	if [ FILE_COUNT -eq 1 ]; then
		# simply rename file for a single flv file
		mv "LAST_FILE" "$MERGED_FILE"
	else
		# merge with ffmpeg
		ffmpeg -f concat -safe 0 -i "$FLV_LIST" -c copy "$MERGED_FILE"
	fi
}

function add_danmaku_to_video {
	execute_if_not_exist "$DANMAKU_ASS" convert_xml_to_ass
	execute_if_not_exist "$MERGED_FILE" merge_videos
	echo "adding danmaku to video; this may take a while"
	# add danmaku
	set -x
	ffmpeg -i "$MERGED_FILE" -vf "ass=$DANMAKU_ASS" "$VIDEO_WITH_DANMAKU"
	set +x
}

# compute duration of final flv
function split_final_video {
	execute_if_not_exist "$VIDEO_WITH_DANMAKU" add_danmaku_to_video
	DURATION_TEMP=$(ffprobe -print_format default -show_format -show_streams "$VIDEO_WITH_DANMAKU" | grep -E "duration=[0-9]+" | head -n 1)
	DURATION=${DURATION_TEMP#*=}
	DURATION=${DURATION%%.*}
	echo "video length is $DURATION"

	# split final flv
	SEGMENT_START=0
	PART_COUNT=1
	SEGMENT_TIME=$(($SEGMENT_LENGTH + $SEGMENT_EXTRA))
	while [ "$SEGMENT_START" -lt "$DURATION" ]
	do
		ffmpeg -ss "$SEGMENT_START" -i "$VIDEO_WITH_DANMAKU" -c copy -t "$SEGMENT_TIME" "part$PART_COUNT.flv"
		SEGMENT_START=$(($SEGMENT_START + $SEGMENT_LENGTH))
		PART_COUNT=$(($PART_COUNT + 1))
	done
}

split_final_video
