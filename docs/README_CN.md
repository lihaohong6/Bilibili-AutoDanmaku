# Bilibili-AutoDanmaku B站录播自动添加弹幕

## 简介

自动制作B站录播的弹幕版。注意；[auto-bilibili-recorder](https://github.com/valkjsaaa/auto-bilibili-recorder) 完成度比本项目高。

## 环境要求

* [B站录播姬](https://rec.danmuji.org)
* `python3.9` 或更高
* `ffmpeg`

B站录播姬是用来录直播的，`python3`和`ffmpeg`都必须安装并添加到path环境变量。注意：装`ffmpeg`时别忘了`ffprobe`。

## 使用方法

### 简单流程

注意：调整录播姬设置时要选保存直播弹幕。
首先[下载最新版本](https://github.com/syccxcc/Bilibili-AutoSub/releases) 。

直播结束后，把录播姬产生的`flv`文件全部复制到程序的`data`文件夹下，然后用录播姬自带的弹幕合并功能把所有`xml`弹幕合并为`danmaku.xml`并和视频一起放在`data`文件夹下。
最后，Windows用户双击运行`run.bat`即可。用OS X或者Linux的用户打开控制台，输入

```
python3 process_recording.py data
```

即可。

然后就可以等程序结束运行。默认的输出文件为`video_with_danmaku.flv`。如果视频过长，程序会自动切割视频，切割后的视频文件名为`part1.flv`、`part2.flv`等等。

### 其它说明

建议把程序和视频文件放在固态硬盘里面，机械硬盘的读写速度太慢，会严重影响程序性能。除此之外，程序需要大量存储空间，至少是所有录播文件加起来的三倍。

编辑config.json文件可以修改程序的设置。

- directory: 录播的保存位置。默认是data文件夹，可以用相对或绝对路径改成另一个文件夹。
- ignore_video_length: 一个数字x。所有长度小于x秒的视频都会被忽略。一般在录播姬产生大量文件时过滤重复的无意义片段。
- add_danmaku: 是否添加弹幕。如果填false，程序只会合并视频并切割。
- xml_file: xml弹幕文件的文件名。
- ass_file: ass字幕文件的文件名。
- merged_video: 合并后视频的文件名。
- video_with_danmaku: 带弹幕的视频的文件名。
- codec: 视频编码。如果用的是英伟达的显卡且支持nvenc，可以改成“h264_nvenc”。详情见[官网](https://trac.ffmpeg.org/wiki/HWAccelIntro) 。
- force_resolution: 是否强制规定弹幕版视频的分辨率。一般为1080p，因此不用修改。如果是手机端直播，不改分辨率会使弹幕可以漂浮的空间变得很小。
- resolution: 如果force_resolution为true，视频的分辨率是什么。
- temp_dir: 临时文件夹的名字。
- smart_merge: 是否智能合并录播视频。如果为false，则直接用ffmpeg合并视频，不会根据视频时间和时长裁剪视频或添加静止帧。
- split: 是否切割完成的视频。
- initial_segment_length: 如果切割视频，第一P的长度应该是多少秒。
- segment_length: 剩余部分的长度应该是多少秒。
- segment_extra: 为了保证视频衔接，每P应该额外添加多少秒。
- danmaku_offset: 弹幕偏移量（单位是秒）。设为负数会使弹幕提前出现，正数会使弹幕延迟出现。
￼
## 原理

1. B站录播姬会产生数个flv文件存储视频数据以及相同数量的同名xml文件存储弹幕信息。因此，第一步就是把多个视频文件合成一个视频以及把多个弹幕文件合成一个文件。录播姬内置了弹幕合并功能，因此程序只需要合并视频。

2. 视频合并。录播姬的弹幕文件保存了开始时间，所以合并后的弹幕文件会和直播时间保持一致。比较麻烦的是视频。如果因为种种原因（例如主播或者录播设备的网烂），视频文件中有长达数秒的缺失，直接合并视频文件会导致弹幕和视频不同步。因此，程序会分析每个视频的开始时间然后智能合并。例如，如果视频A在第0秒开始，时长10秒，而下一个视频B在第20秒开始，那么可以断定中间有10秒录播缺失。智能合并程序会截取视频A的最后一帧，然后生成一段长达10秒的静止帧视频。最终合并时会把10秒静止帧包含进去，这样就可以让视频时间和弹幕保持一致了。同理，如果视频A时长30秒，那么程序会判断视频A的最后10秒和视频B重叠，因此合并时只截取视频A的前20秒。 最后，程序会用ffmpeg的concat功能把所有视频（包括静止帧）合并成一个文件。

3. 弹幕合并：手动用录播姬合并。自动合并功能会（在未来遥远的某一天）有的。或许可以直接用BililiveRecorder.Cli达成？

4. 弹幕xml转ass。用[danmaku2ass](https://github.com/m13253/danmaku2ass) 做的转换。程序内置了`danmaku2ass`。示例：
```shell
python3 danmaku2ass.py -o danmaku.ass -s 1920x1080 -f Bilibili -fn "Microsoft YaHei" -fs 64 -a 0.7 -dm 10 -ds 8 danmaku.xml
```

5. 添加弹幕。ass字幕先用ffmpeg根据偏移量预处理。然后再用libass的ass滤镜添加弹幕，需要注意的是fps要调成60而不是默认的24，否则弹幕的移动看起来会很卡。除此之外，如果设置中选取了强制分辨率转换，程序还会使用scale滤镜调整分辨率和pad滤镜添加黑色背景。

6. 分割最终视频。没什么好说的。用ffprobe获取总时长，然后计算每一段的开始时间，最后用ffmpeg切割。
￼
## 未实装功能

1. 根据弹幕长度自动添加偏移。例如，“3”、“打卡”和“啊啊啊啊啊”的偏移量设成-2左右就够了。但是一段长且复杂的弹幕的偏移量可能需要改成-10以获得最佳观看体验。

2. 添加更多可更改的设置。例如：弹幕字体，弹幕字号，弹幕在屏幕上的停留时间（更长则弹幕速度更慢，更短则弹幕速度更快）。

3. 添加自动合并xml弹幕文件的功能。虽然打开录播姬点几下就行，但还是很麻烦。

4. 其它暂时没有想到的。

如果对以上任何功能有需求（包括没写的）都可以在Issues提。


