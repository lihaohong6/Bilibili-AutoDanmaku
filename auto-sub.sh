CONFIG_FILE=./config.sh

# shellcheck source=./config.sh
. "$CONFIG_FILE"

chmod +x "$DANMAKU_CONVERSION_SCRIPT"
chmod +x "$SMART_MERGING_SCRIPT"

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
	assert_file_exist "$DANMAKU_CONVERSION_SCRIPT"
	echo "converting from xml to ass"
	python3 "$DANMAKU_CONVERSION_SCRIPT" -o "$TEMP_DANMAKU_ASS" -s 1920x1080 -f Bilibili -fn "Microsoft YaHei" -fs 64 -a 0.7 -dm 10 -ds 8 "$DANMAKU_FILE"
	# TODO: offset should be based on danmaku length: the longer the danmaku, the earlier it should have appeared
	assert_file_exist "$TEMP_DANMAKU_ASS"
	ffmpeg -hide_banner -loglevel warning -itsoffset "$DANMAKU_OFFSET" -i "$TEMP_DANMAKU_ASS" -c copy "$DANMAKU_ASS"
}

function get_flv_files() {
  FLV_LIST=$(find . -type f -name "*.flv" | sort)
  IFS=$'\n'
}

function get_duration {
  DURATION_RETURN=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$1")
}

function merge_videos {
	# find all flv files and put their names in a txt file
	rm -f "$FLV_LIST_FILE_NAME"

	get_flv_files
	FILE_COUNT=$(echo "$FLV_LIST" | wc -l)
	echo "$FILE_COUNT flv file(s) found"

	if [ "$FILE_COUNT" -eq 0 ]; then
    echo "You need as least 1 file with the extension .flv"
    exit 1
	elif [ "$FILE_COUNT" -eq 1 ]; then
		# simply rename file for a single flv file
		mv "${FLV_LIST[0]}" "$MERGED_FILE"
	else
		# merge with ffmpeg
		# TODO: ask dora stackoverflow to see if there's a way to keep the timestamps
		if [ "$SMART_MERGING" -eq 0 ]; then
		  for FILE in $FLV_LIST; do
	      printf "file '%s'\n" "$FILE" >> "$FLV_LIST_FILE_NAME"
  	  done;
		else
		  FLV_DURATIONS=""
		  for FILE in $FLV_LIST; do
		    get_duration "$FILE"
		    FLV_DURATIONS="${FLV_DURATIONS} ${DURATION_RETURN}"
		  done;
		  python3 "$SMART_MERGING_SCRIPT" -l "$FLV_LIST" -d "$FLV_DURATIONS" -f "$FLV_LIST_FILE_NAME"
		fi
		echo "merging flv videos"
		# this will generate lots of warnings about non-monotonous DTS and these warnings are ignored
		ffmpeg -hide_banner -loglevel error -safe 0 -f concat -i "$FLV_LIST_FILE_NAME" -c copy "$MERGED_FILE"
	fi
}

function add_danmaku_to_video {
	execute_if_not_exist "$DANMAKU_ASS" convert_xml_to_ass
	execute_if_not_exist "$MERGED_FILE" merge_videos
	# use codec of original video and leave bit rate to the encoder
	CODEC="$(ffprobe -loglevel error -select_streams v:0 -show_entries stream=codec_name -of default=nk=1:nw=1 "$MERGED_FILE")"
	echo "adding danmaku to video; this may take a while"
	# add danmaku
	set -x
	ffmpeg -hide_banner -i "$MERGED_FILE" -vf "ass=$DANMAKU_ASS" -vcodec "$CODEC" "$VIDEO_WITH_DANMAKU"
	set +x
}

# compute duration of final flv
function split_final_video {
	execute_if_not_exist "$VIDEO_WITH_DANMAKU" add_danmaku_to_video
	get_duration "$VIDEO_WITH_DANMAKU"
	DURATION=${DURATION_RETURN%%.*}
	echo "video length is $DURATION_RETURN"

	# split final flv
	# TODO: program should automatically determine initial segment length based on video size given that upload limit is 8GB
	SEGMENT_START=0
	PART_COUNT=1
	SEGMENT_TIME=$((INITIAL_SEGMENT_LENGTH + SEGMENT_EXTRA))
	if [ "$SEGMENT_TIME" -gt "$DURATION" ]; then
	  echo "video is short; no need to split"
		return 0
	fi
	echo "splitting video"
	while [ "$SEGMENT_START" -lt "$DURATION" ]
	do
		ffmpeg -hide_banner -ss "$SEGMENT_START" -i "$VIDEO_WITH_DANMAKU" -c copy -t "$SEGMENT_TIME" "part$PART_COUNT.flv"
		SEGMENT_START=$((SEGMENT_START + SEGMENT_TIME - SEGMENT_EXTRA))
		PART_COUNT=$((PART_COUNT + 1))
		if [ "$PART_COUNT" -eq 1 ]; then
			SEGMENT_TIME=$((SEGMENT_LENGTH + SEGMENT_EXTRA))
		fi
	done
}

split_final_video