DANMAKU_FILE=./danmaku.xml
DANMAKU_ASS=./danmaku.ass
PYTHON_SCRIPT=./danmaku2ass.py
FLV_LIST=./files.txt
MERGED_FILE=./merged.flv
FILE_NAME=PLACE_HOLDER

function assert_file_exist {
	if [ ! -f "$FILE_NAME" ]; then
		echo "no file named $FILE_NAME present"
		exit 1
	fi
}

if [ ! -f "$DANMAKU_ASS" ]; then
	if [ ! -f "$DANMAKU_FILE" ]; then
		echo "no danmaku file present"
		exit 1
	fi
	echo "XML danmaku file found, now converting"
	if [ ! -f "$PYTHON_SCRIPT" ]; then
		echo "no python script found"
		exit 1
	fi
	echo "converting from xml to ass"
	"$PYTHON_SCRIPT" -o "$DANMAKU_ASS" -s 1920x1080 -f Bilibili -fn "Microsoft Yahei" "$DANMAKU_FILE"
fi
if [ ! -f "$DANMAKU_ASS" ]; then
	echo "no converted ass file"
	exit 1
fi
echo "ass file found; proceeding..."
for FILE in ./*; do
    if [[ "$FILE" == *.flv ]]; then
        printf "$FILE\n" >> "$FLV_LIST" 
    fi
done;
