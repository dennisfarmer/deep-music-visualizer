
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
GANDIR=./video-generation

build: audio video
	@make cleanall
	# all done!

mscore:
	mkdir -p $(WAV)
	# generating individual wav files
	$(foreach file, $(wildcard $(MUSE)/*.mscz),\
		$(MSCORE) $(file) -o $(WAV)/$(shell basename $(file) .mscz).wav >/dev/null 2>&1;)

midi:
	# generating midi file for audio panning
	@$(MSCORE) $(MSCZDIR)/$(TITLE).mscz -o $(MSCZDIR)/measures.midi

gan:
	conda activate ganmusicvis
	cd $(GANDIR)
	python visualize.py \
		--song ./Impassive.wav \
		--tempo_sensitivity 0.5 \
		--depth 0.8 \
		--resolution 512 \
		--output_file ./Impassive.mp4 \
		--use_previous_classes 1 \
		--use_previous_vectors 1
	cd -
	conda deactivate

audio: midi
	conda activate ganmusicvis
	# Combining vibe tracks and adding tremolo to vibraphone parts
	# (3 minutes)
	make vibes
	# Combining glockxylo tracks
	make glockxylo
	# Combining marimba tracks
	# (2 minutes)
	make marimba
	# Adding reverb to tracks and combining them together
	make reverb
	conda deactivate
	@make clean

amerge: audio merge

vibes:
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/$(TITLE)-Vibes.wav \
		-filter:a "volume=0.8" $(WAV)/temp02.wav
	#python 8d.py -i $(WAV)/$(TITLE)-8d-Vibes.wav -o $(WAV)/temp01.wav -e vibes
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/$(TITLE)-8d-Vibes.wav \
		-filter:a "volume=0.7" $(WAV)/temp03.wav
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/temp02.wav \
		-channel_layout stereo -i $(WAV)/temp03.wav \
		-filter_complex amix=inputs=2:duration=longest $(WAV)/temp01.wav
	sox -r $(HERTZ) $(WAV)/temp01.wav $(WAV)/Vibes-Dry.wav tremolo 6 33
	# adding panning audio effect and reverb
	sox $(WAV)/Vibes-Dry.wav $(WAV)/temp01.wav reverb $(SOXREVERB)
	python 8d.py -i $(WAV)/temp01.wav -o $(WAV)/Vibes-Wet.wav -e vibes
	@make clean

glockxylo:
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/$(TITLE)-GlockXylo.wav \
		-filter:a "volume=0.2" $(WAV)/temp02.wav
	cp $(WAV)/temp02.wav $(WAV)/temp04.wav
	sox $(WAV)/temp02.wav $(WAV)/temp01.wav reverb $(SOXREVERB)
	python 8d.py -i $(WAV)/temp01.wav -o $(WAV)/temp02.wav -e glockxyloright
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/$(TITLE)-8d-GlockXylo.wav \
		-filter:a "volume=0.2" $(WAV)/temp03.wav
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/temp04.wav \
		-channel_layout stereo -i $(WAV)/temp03.wav \
		-filter_complex amix=inputs=2:duration=longest $(WAV)/GlockXylo-Dry.wav
	rm $(WAV)/temp04.wav
	sox $(WAV)/temp03.wav $(WAV)/temp01.wav reverb $(SOXREVERB)
	python 8d.py -i $(WAV)/temp01.wav -o $(WAV)/temp03.wav -e glockxyloleft
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/temp02.wav \
		-channel_layout stereo -i $(WAV)/temp03.wav \
		-filter_complex amix=inputs=2:duration=longest $(WAV)/GlockXylo-Wet.wav
	@make clean

marimba:
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/$(TITLE)-Marimba.wav \
		-filter:a "volume=1" $(WAV)/temp02.wav
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/$(TITLE)-8d-Marimba.wav \
		-filter:a "volume=0.7" $(WAV)/temp03.wav
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/temp02.wav \
		-channel_layout stereo -i $(WAV)/temp03.wav \
		-filter_complex amix=inputs=2:duration=longest $(WAV)/Marimba-Dry.wav
	# adding panning audio effect and reverb
	sox $(WAV)/Marimba-Dry.wav $(WAV)/temp01.wav reverb $(SOXREVERB)
	python 8d.py -i $(WAV)/temp01.wav -o $(WAV)/Marimba-Wet.wav -e marimba
	@make clean

reverb:
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/Vibes-Dry.wav \
		-channel_layout stereo -i $(WAV)/GlockXylo-Dry.wav \
		-channel_layout stereo -i $(WAV)/Marimba-Dry.wav \
		-filter_complex amix=inputs=3:duration=longest $(WAV)/$(TITLE)-Dry.wav
	ffmpeg $(FFMPEGFLAGS) \
		-channel_layout stereo -i $(WAV)/Vibes-Wet.wav \
		-channel_layout stereo -i $(WAV)/GlockXylo-Wet.wav \
		-channel_layout stereo -i $(WAV)/Marimba-Wet.wav \
		-filter_complex amix=inputs=3:duration=longest $(WAV)/$(TITLE)-Wet.wav
	cp $(WAV)/$(TITLE)-Wet.wav .
	@make clean

video:
	# Converting video from mp4 to mkv
	ffmpeg $(FFMPEGFLAGS) \
		-i $(GANDIR)/$(TITLE).mp4 \
		-vcodec copy $(MKV)/$(TITLE)-Right.mkv
	make mirror
	make vhstack
	make upscale
	make merge
	make videoeffects
	@make clean

mirror:
	# Horizontally stacking original and horizontally flipped videos (might take a while)
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE)-Right.mkv \
		-vf hflip -c:a copy $(MKV)/$(TITLE)-Left.mkv
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE)-Left.mkv \
		-i $(MKV)/$(TITLE)-Right.mkv \
		-filter_complex hstack=inputs=2 $(MKV)/$(TITLE)-Center.mkv

vhstack: vstack hstack

vstack:
	# Filling video to 16:9 aspect ratio by mirroring top and botom (might take a while)
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE)-Center.mkv \
		-filter:v "crop=1024:73:0:0, vflip" \
		-c:a copy $(MKV)/$(TITLE)-Top.mkv
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE)-Center.mkv \
		-filter:v "crop=1024:90:0:422, vflip" \
		-c:a copy $(MKV)/$(TITLE)-Bottom.mkv
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE)-Top.mkv \
		-i $(MKV)/$(TITLE)-Center.mkv \
		-i $(MKV)/$(TITLE)-Bottom.mkv \
		-filter_complex vstack=inputs=3 $(MKV)/$(TITLE)-Vstack.mkv
	# result: 1024 x 675

hstack:
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE)-Vstack.mkv \
		-filter:v "crop=88:675:0:0, hflip" \
		-c:a copy $(MKV)/$(TITLE)-Left2.mkv
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE)-Vstack.mkv \
		-filter:v "crop=88:675:936:0, hflip" \
		-c:a copy $(MKV)/$(TITLE)-Right2.mkv
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE)-Left2.mkv \
		-i $(MKV)/$(TITLE)-Vstack.mkv \
		-i $(MKV)/$(TITLE)-Right2.mkv \
		-filter_complex hstack=inputs=3 $(MKV)/$(TITLE)-HVstack.mkv
	# result: 1200 x 675

upscale:
	# upscaling video to 1080p
	# (14 minutes)
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE)-HVStack.mkv \
		-vf scale=1920:1080:flags=bicubic $(MKV)/$(TITLE).mkv

merge:
	# Adding formatted audio tracks to video
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE).mkv \
		-channel_layout stereo -i $(WAV)/$(TITLE)-Wet.wav \
		-c:v copy -map 0:v:0 -map 1:a:0 -shortest $(MKV)/$(TITLE)-Merged.mkv
	mv $(MKV)/$(TITLE)-Merged.mkv $(MKV)/$(TITLE).mkv

videoeffects:
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE).mkv \
		-vf "drawtext=fontfile=media/Agency.ttf:text=$(TITLE):alpha=0.8:shadowcolor=#E2DCD2:shadowx=-10:shadowy=-10:fontcolor=#C75349:fontsize=150:x=723:y=865:enable='between(t,0,0.62)'" \
		$(MKV)/$(TITLE)-Text.mkv
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE)-Text.mkv \
		-t 0.5 $(MKV)/$(TITLE)-Title.mkv
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE)-Text.mkv \
		-ss 0.5 $(MKV)/$(TITLE)-PostTitle.mkv
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE)-Title.mkv \
		-filter:v "setpts=7.5*PTS" $(MKV)/$(TITLE)-TitleSlow.mkv
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE)-TitleSlow.mkv \
		-vf "fade=t=in:st=0:d=2" -c:a copy $(MKV)/$(TITLE)-Title.mkv
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE)-PostTitle.mkv \
		-ss 42.4 $(MKV)/$(TITLE)-EndForward.mkv
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE)-EndForward.mkv \
		-vf reverse $(MKV)/$(TITLE)-EndBackward.mkv
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE)-Title.mkv \
		-i $(MKV)/$(TITLE)-PostTitle.mkv \
		-i $(MKV)/$(TITLE)-EndBackward.mkv \
		-i $(MKV)/$(TITLE)-EndForward.mkv \
		-filter_complex "concat=n=4:v=1:a=1" $(MKV)/$(TITLE)-Concat.mkv
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE)-Concat.mkv \
		-vf "fade=t=out:st=44:d=4" -c:a copy $(MKV)/$(TITLE)-FadeOut.mkv
	ffmpeg $(FFMPEGFLAGS) \
		-i $(MKV)/$(TITLE)-FadeOut.mkv \
		-t 48.4 $(MKV)/$(TITLE)-Done.mkv
	cp $(MKV)/$(TITLE)-Done.mkv ./$(TITLE).mkv

clean:
	rm -f $(WAV)/temp01.wav $(WAV)/temp02.wav $(WAV)/temp03.wav
	rm -f $(TITLE)-Right.mkv $(TITLE)-Left.mkv $(TITLE)-Top.mkv $(TITLE)-Bottom.mkv

cleanall:
	make clean
	rm -f $(MSCZDIR)/measures.midi
	rm -f \
		$(WAV)/Vibes-Dry.wav \
		$(WAV)/Vibes-Wet.wav \
		$(WAV)/GlockXylo-Dry.wav \
		$(WAV)/GlockXylo-Wet.wav \
		$(WAV)/Marimba-Dry.wav \
		$(WAV)/Marimba-Wet.wav \
		$(WAV)/$(TITLE)-Dry.wav \
		$(WAV)/$(TITLE)-Wet.wav \
		$(WAV)/$(TITLE)-Vibes.wav \
		$(WAV)/$(TITLE)-8d-Vibes.wav \
		$(WAV)/$(TITLE)-GlockXylo.wav \
		$(WAV)/$(TITLE)-8d-GlockXylo.wav \
		$(WAV)/$(TITLE)-Marimba.wav \
		$(WAV)/$(TITLE)-8d-Marimba.wav
	rm -f \
		$(MKV)/$(TITLE)-Merged.mkv \
		$(MKV)/$(TITLE)-Mirrored.mkv \
		$(MKV)/$(TITLE)-Bottom.mkv \
		$(MKV)/$(TITLE)-Center.mkv \
		$(MKV)/$(TITLE)-Concat.mkv \
		$(MKV)/$(TITLE)-EndBackward.mkv \
		$(MKV)/$(TITLE)-EndForward.mkv \
		$(MKV)/$(TITLE)-HVstack.mkv \
		$(MKV)/$(TITLE)-Left.mkv \
		$(MKV)/$(TITLE)-Left2.mkv \
		$(MKV)/$(TITLE)-PostTitle.mkv \
		$(MKV)/$(TITLE)-Right.mkv \
		$(MKV)/$(TITLE)-Right2.mkv \
		$(MKV)/$(TITLE)-Text.mkv \
		$(MKV)/$(TITLE)-Title.mkv \
		$(MKV)/$(TITLE)-TitleSlow.mkv \
		$(MKV)/$(TITLE)-Top.mkv \
		$(MKV)/$(TITLE)-Vstack.mkv \
		$(MKV)/$(TITLE)-FadeOut.mkv \
		$(MKV)/$(TITLE)-Done.mkv \
		$(MKV)/$(TITLE).mkv

