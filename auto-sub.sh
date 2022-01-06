# WARNING: this script is deprecated. Use process_recording.py instead.

CONFIG_FILE=./config.sh

# shellcheck source=./config.sh
. "$CONFIG_FILE"

chmod +x "$DANMAKU_CONVERSION_SCRIPT"
chmod +x "$SMART_MERGING_SCRIPT"

#######################################
# Assert that a file exists. If it does not, exit the program.
# Arguments:
#   $1: name of the file that should exist
#   $2: an optional error message to be printed if file does not exist
#######################################
function assert_file_exist {
	if [ ! -f "$1" ]; then
		echo "no file named $1 present"
		if [ $# -eq 2 ]; then
			echo "$2"
		fi
		exit 1
	fi
}

#######################################
# Execute a function to create a file if that file does not exist
# Globals:
#   $FILE_NAME
#   $FUNCTION_NAME
# Arguments:
#   $1: name of the needed file
#   $2: function to create the file
# Outputs:
#   No effect if file already exists. Otherwise the function is executed.
#######################################
function execute_if_not_exist {
	FILE_NAME=$1
	FUNCTION_NAME=$2
	if [ ! -f "$FILE_NAME" ]; then
		$FUNCTION_NAME
	fi
	assert_file_exist "$FILE_NAME"
}

#######################################
# Use find to get a list of files with a certain extension in the current directory
# Globals:
#   $FILE_LIST
#   $IFS
# Arguments:
#   $1: file pattern
# Outputs:
#   Store a \n delimited list of file names in $FILE_LIST
#   Change IFS so that array splitting works
#######################################
function get_files() {
  FILE_LIST=$(find . -not -path '*/\.*' -type f -name "$1" | sort)
  IFS=$'\n'
}

function merge_danmakus() {
  get_files "*.xml"
  # FIXME: there's gotta be a better way to do this that doesn't involve invoking BililiveRecorder
  IFS=$'\n'
  BililiveRecorder.Cli tool danmaku-merge "$DANMAKU_FILE" ${FILE_LIST[@]}
}

function convert_xml_to_ass() {
	# try to find ass file; if not exist, convert the xml file to ass
	execute_if_not_exist "$DANMAKU_FILE" merge_danmakus
	assert_file_exist "$DANMAKU_FILE"
	echo "XML danmaku file found, now converting"
	assert_file_exist "$DANMAKU_CONVERSION_SCRIPT"
	echo "converting from xml to ass"
	python3 "$DANMAKU_CONVERSION_SCRIPT" -o "$TEMP_DANMAKU_ASS" -s 1920x1080 -f Bilibili -fn "Microsoft YaHei" -fs 64 -a 0.7 -dm 10 -ds 8 "$DANMAKU_FILE"
	# danmaku tends to be sent after the fact, so use an offset to make then appear early
	# TODO: offset should be based on danmaku length: the longer the danmaku, the earlier it should have appeared
	assert_file_exist "$TEMP_DANMAKU_ASS"
	ffmpeg -hide_banner -loglevel warning -itsoffset "$DANMAKU_OFFSET" -i "$TEMP_DANMAKU_ASS" -c copy "$DANMAKU_ASS"
}

#######################################
# Use ffprobe to obtain the duration of a video
# Globals:
#   $DURATION_RETURN
# Arguments:
#   $1: name of the video file
# Outputs:
#   Write length of video to $DURATION_RETURN
#######################################
function get_duration {
  DURATION_RETURN=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$1")
}

function merge_videos {
	# find all flv files
	get_files "*.flv"
	FILE_COUNT=$(echo "$FILE_LIST" | wc -l)
	echo "$FILE_COUNT flv file(s) found"

	if [ "$FILE_COUNT" -eq 0 ]; then
    echo "You need as least 1 file with the extension .flv"
    exit 1
	elif [ "$FILE_COUNT" -eq 1 ]; then
		# simply rename file for a single flv file
		mv "${FILE_LIST[0]}" "$MERGED_FILE"
	else
		# merge with ffmpeg
		rm -f "$FLV_LIST_FILE_NAME"
		# if smart merging is off, just concat
		if [ "$SMART_MERGING" -eq 0 ]; then
		  for FILE in $FILE_LIST; do
	      printf "file '%s'\n" "$FILE" >> "$FLV_LIST_FILE_NAME"
  	  done;
		else
		  # if smart merging is on, use Python program to keep video in sync with danmaku
		  FLV_DURATIONS=""
		  for FILE in $FILE_LIST; do
		    get_duration "$FILE"
		    FLV_DURATIONS="${FLV_DURATIONS} ${DURATION_RETURN}"
		  done;
		  python3 "$SMART_MERGING_SCRIPT" -l "$FILE_LIST" -d "$FLV_DURATIONS" -f "$FLV_LIST_FILE_NAME"
		fi
		echo "merging flv videos"
		# this will generate lots of warnings about non-monotonous DTS so these warnings are ignored
		ffmpeg -hide_banner -loglevel error -safe 0 -f concat -i "$FLV_LIST_FILE_NAME" -c copy "$MERGED_FILE"
	fi
}

function add_danmaku_to_video {
  # there should be a video file and a danmaku file
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


#######################################
# Split final file into parts for convenient upload.
# Globals:
#   $VIDEO_WITH_DANMAKU
#   $INITIAL_SEGMENT_LENGTH
#   $SEGMENT_LENGTH
#   $SEGMENT_EXTRA
# Arguments:
#   None
# Outputs:
#   Splits $VIDEO_WITH_DANMAKU into several parts named part1.flv, part2.flv, ...
#######################################
function split_final_video {
  # split the final
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
		ffmpeg -hide_banner -loglevel warning -ss "$SEGMENT_START" -i "$VIDEO_WITH_DANMAKU" -c copy -t "$SEGMENT_TIME" "part$PART_COUNT.flv"
		SEGMENT_START=$((SEGMENT_START + SEGMENT_TIME - SEGMENT_EXTRA))
		PART_COUNT=$((PART_COUNT + 1))
		if [ "$PART_COUNT" -eq 2 ]; then
			SEGMENT_TIME=$((SEGMENT_LENGTH + SEGMENT_EXTRA))
		fi
	done
}

# Makefile style script. Files are created based on demand.
split_final_video
