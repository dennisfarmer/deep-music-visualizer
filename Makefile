
TITLE=Impassive
.SILENT: clean cleanall
.PHONY: clean cleanall
FFMPEGFLAGS = -y -hide_banner -loglevel warning
MSCORE=/Applications/Musescore\ 3.app/Contents/MacOS/mscore
SOXREVERB = 60 50 55
HERTZ=48000 
MSCZDIR=./media
MUSE=$(MSCZDIR)/muse
WAV=$(MSCZDIR)/wav
MKV=$(MSCZDIR)/mkv
# To add delay to reverb tracks:
#sox -n -r 48000 -c 2 silence.wav trim 0 0.020
#sox -r 48000 silence.wav temp01.wav temp02.wav

# 8d tracks have 8d effect added with 8d.py
# Vibraphone tracks have tremolo effect added with sox filter

# 8D EFFECT OPTIONS:
# 8d tracks: set period to 200ms since it lines up with mini-climax at mm. 7
# normal: either 200ms or 300ms, both 8d/normal tracks seem to line up at measure 7 since 200+300 are multiples of each other
# sine wave starts at center (x=0) and trails towards right ear first

# Video Upscaling:
# Bicubic Interpolation
# 1080 / 1920 = 0.5625
# (512 + 512) * 0.5625 = 576
# 576 - 512 = 64
# 64 / 2 = 32

# bottom: 0,32, 1024x32
# top: 0,512, 1024x32




build: audio video
	@make cleanall
	# all done!

mscore:
	# generating individual wav files
	$(foreach file, $(wildcard $(MUSE)/*.mscz),\
		$(MSCORE) $(file) -o $(WAV)/$(shell basename $(file) .mscz).wav >/dev/null 2>&1;)

midi:
	# generating midi file for audio panning
	@$(MSCORE) $(MSCZDIR)/$(TITLE).mscz -o $(MSCZDIR)/measures.midi

#python visualize.py --song ./Impassive.wav --tempo_sensitivity 0.5 --depth 0.8 --resolution 512 --output_file ./Impassive.mp4 --sort_classes_by_power 0 --num_classes 12 --classes 663 947 642782 624 909 541 815 978 789 508 429
gan:
	cd video-generation
	python visualize.py --song ./Impassive.wav --tempo_sensitivity 0.5 --depth 0.8 --resolution 512 --output_file ../Impassive.mp4 --use_previous_classes 1 --use_previous_vectors 1
	cd -

audio: midi
	# Combining vibe tracks and adding tremolo to vibraphone parts
	make vibes
	# Combining glockxylo tracks
	make glockzylo
	# Combining marimba tracks
	make marimba
	# Adding reverb to tracks and combining them together
	make reverb
	@make clean

amerge: audio merge

vibes:
	python 8d.py -i $(WAV)/$(TITLE)-Vibes.wav -o $(WAV)/temp01.wav -e vibes
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/temp01.wav \
		-filter:a "volume=0.9" $(WAV)/temp02.wav
	python 8d.py -i $(WAV)/$(TITLE)-8d-Vibes.wav -o $(WAV)/temp01.wav -e vibes
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/temp01.wav \
		-filter:a "volume=0.8" $(WAV)/temp03.wav
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/temp02.wav \
		-channel_layout stereo -i $(WAV)/temp03.wav \
		-filter_complex amix=inputs=2:duration=longest $(WAV)/temp01.wav
	sox -r $(HERTZ) temp01.wav $(WAV)/Vibes-Dry.wav tremolo 6 33
	@make clean

glockxylo:
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/$(TITLE)-GlockXylo.wav \
		-filter:a "volume=1" $(WAV)/temp02.wav
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/$(TITLE)-8d-GlockXylo.wav \
		-filter:a "volume=0.6" $(WAV)/temp03.wav
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/temp02.wav \
		-channel_layout stereo -i $(WAV)/temp03.wav \
		-filter_complex amix=inputs=2:duration=longest $(WAV)/GlockXylo-Dry.wav
	@make clean

marimba:
	python 8d.py -i $(WAV)/$(TITLE)-Marimba.wav -o $(WAV)/temp01.wav -e marimba
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/temp01.wav \
		-filter:a "volume=1" $(WAV)/temp02.wav
	python 8d.py -i $(WAV)/$(TITLE)-8d-Marimba.wav -o $(WAV)/temp01.wav -e marimba
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/temp01.wav \
		-filter:a "volume=0.7" $(WAV)/temp03.wav
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/temp02.wav \
		-channel_layout stereo -i $(WAV)/temp03.wav \
		-filter_complex amix=inputs=2:duration=longest $(WAV)/Marimba-Dry.wav
	@make clean

reverb:
	sox $(WAV)/Vibes-Dry.wav $(WAV)/Vibes-Wet.wav reverb $(SOXREVERB)
	sox $(WAV)/GlockXylo-Dry.wav $(WAV)/GlockXylo-Wet.wav reverb $(SOXREVERB)
	sox $(WAV)/Marimba-Dry.wav $(WAV)/Marimba-Wet.wav reverb $(SOXREVERB)
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/Vibes-Dry.wav \
		-channel_layout stereo -i $(WAV)/GlockXylo-Dry.wav \
		-channel_layout stereo -i $(WAV)/Marimba-Dry.wav \
		-filter_complex amix=inputs=3:duration=longest $(WAV)/$(TITLE)-Dry.wav
	sox $(WAV)/$(TITLE)-Dry.wav $(WAV)/$(TITLE)-Wet.wav reverb $(SOXREVERB)
	cp $(WAV)/$(TITLE)-Wet.wav .
	@make clean

mirror:
	# Horizontally stacking original and horizontally flipped videos (might take a while)
	ffmpeg $(FFMPEGFLAGS) -i $(TITLE)-Right.mkv -vf hflip -c:a copy $(TITLE)-Left.mkv
	ffmpeg $(FFMPEGFLAGS) -i $(TITLE)-Left.mkv -i $(TITLE)-Right.mkv -filter_complex hstack=inputs=2 $(TITLE)-Center.mkv

hvstack:
	# Filling video to 16:9 aspect ratio by mirroring top and botom (might take a while)
	ffmpeg $(FFMPEGFLAGS) -i $(TITLE)-Center.mkv -filter:v "crop=1024:32:0:0, vflip" -c:a copy $(TITLE)-Top.mkv
	ffmpeg $(FFMPEGFLAGS) -i $(TITLE)-Center.mkv -filter:v "crop=1024:32:0:480, vflip" -c:a copy $(TITLE)-Bottom.mkv
	ffmpeg $(FFMPEGFLAGS) -i $(TITLE)-Top.mkv -i $(TITLE)-Center.mkv -i $(TITLE)-Bottom.mkv -filter_complex vstack=inputs=3 $(TITLE)-Vstack.mkv
	@make clean
	# output: hvstack.mkv
	#top: 156

vtest:
	# Converting video from mp4 to mkv
	ffmpeg $(FFMPEGFLAGS) -i $(TITLE).mp4 -vcodec copy $(TITLE)-Right.mkv
	make mirror


video:
	# Converting video from mp4 to mkv
	ffmpeg $(FFMPEGFLAGS) -i $(TITLE).mp4 -vcodec copy $(TITLE)-Right.mkv
	make mirror
	make hvstack
	make upscale
	make merge
	@make clean

upscale:
	ffmpeg $(FFMPEGFLAGS) -i $(TITLE)-HVStack.mkv -vf scale=1920:1080:flags=bicubic $(TITLE)-Bicubic.mkv
	mv $(TITLE)-Bicubic.mkv $(TITLE).mkv

merge:
	# Adding formatted audio tracks to video
	ffmpeg $(FFMPEGFLAGS) -i $(TITLE).mkv -channel_layout stereo -i $(WAV)/$(TITLE)-Wet.wav -c:v copy -map 0:v:0 -map 1:a:0 -shortest $(MKV)/$(TITLE)-Merged.mkv
	mv $(MKV)/$(TITLE)-Merged.mkv $(TITLE).mkv

clean:
	rm -f $(WAV)/temp01.wav $(WAV)/temp02.wav $(WAV)/temp03.wav
	rm -f $(TITLE)-Right.mkv $(TITLE)-Left.mkv $(TITLE)-Top.mkv $(TITLE)-Bottom.mkv

cleanall:
	make clean
	rm -f $(TITLE)-Merged.mkv $(TITLE)-Dry.wav $(TITLE)-Wet.wav Vibes-Dry.wav Vibes-Wet.wav NotVibes-Dry.wav NotVibes-Wet.wav
	rm -f $(TITLE)-Merged.mkv $(TITLE)-Mirrored.mkv


#-map 0:v:0 maps the first (index 0) video stream from the input to the first (index 0) video stream in the output.
#-map 1:a:0 maps the second (index 1) audio stream from the input to the first (index 0) audio stream in the output.

# swap channels on stereo audio file
#ffmpeg -i INPUT -map_channel 0.0.1 -map_channel 0.0.0 OUTPUT

#ffmpeg $(FFMPEGFLAGS) -i $(TITLE).mkv -vf scale=1920:1080:flags=lanczos $(TITLE)-Lanczos.mkv

#compare:
	#ffmpeg $(FFMPEGFLAGS) -i $(TITLE)-Bicubic.mkv -filter:v "crop=960:1080:0:0" -c:a copy $(TITLE)-BicubicLeft.mkv
	#ffmpeg $(FFMPEGFLAGS) -i $(TITLE)-Lanczos.mkv -filter:v "crop=960:1080:960:0" -c:a copy $(TITLE)-LanczosRight.mkv
	#ffmpeg $(FFMPEGFLAGS) -i $(TITLE)-BicubicLeft.mkv -i $(TITLE)-LanczosRight.mkv -filter_complex hstack=inputs=2 $(TITLE)-Compare.mkv
	# Adding formatted audio tracks to video
	#ffmpeg $(FFMPEGFLAGS) -i $(TITLE)-Compare.mkv -channel_layout stereo -i $(TITLE)-Wet.wav -c:v copy -map 0:v:0 -map 1:a:0 -shortest $(TITLE)-Merged.mkv

#filter:
	#ffmpeg $(FFMPEGFLAGS) -i $(TITLE)-Bicubic.mkv -vf curves=vintage $(TITLE)-BicubicFiltered.mkv
	# Adding formatted audio tracks to video
	#ffmpeg $(FFMPEGFLAGS) -i $(TITLE)-BicubicFiltered.mkv -channel_layout stereo -i $(TITLE)-Wet.wav -c:v copy -map 0:v:0 -map 1:a:0 -shortest $(TITLE)-Merged.mkv
