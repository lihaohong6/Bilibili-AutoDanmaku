.PHONY: build

TARGET_DIR=build

build:
	rm -rf ${TARGET_DIR}
	mkdir ${TARGET_DIR}
	cp -r models utils README.md process_recording.py ${TARGET_DIR}
	cp config.default.json ${TARGET_DIR}
	mv ${TARGET_DIR}/config.default.json ${TARGET_DIR}/config.json

windows: build
	cp run.bat lib/win/* ${TARGET_DIR}