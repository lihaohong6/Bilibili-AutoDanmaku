.PHONY: build

TARGET_DIR=../Bilibil-AutoDanmaku_v1.0.0_${MAKECMDGOALS}

build:
	rm -rf ${TARGET_DIR}
	rm -rf utils/__pycache__ models/__pycache__
	mkdir ${TARGET_DIR}
	cp -r utils models docs ${TARGET_DIR}
	cp README.md LICENSE process_recording.py ${TARGET_DIR}
	cp config.default.json ${TARGET_DIR}
	mv ${TARGET_DIR}/config.default.json ${TARGET_DIR}/config.json
	mkdir ${TARGET_DIR}/data

windows: build
	cp scripts/run.bat ${TARGET_DIR}

posix: build
	cp scripts/run.sh ${TARGET_DIR}

windows-lib: build
	cp lib/win/* ${TARGET_DIR}
