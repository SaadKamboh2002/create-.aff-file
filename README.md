* aaf_machine.py is the main file yoy need to run to make the .aaf file, all the data and references will be set in timeline_metadata.json, currently in the json file it contains details
  about two videos and two audios, the first video(total length 10s) plays first for 5 seconds, then after 5 seconds of video playback the audio starts playing for 10 seconds while the
  remaining of the 5s of video plays, making the total runtime 15s, after that the video2 and sound2 start playing at the same time for 5s making the total timeline 20s long, you can set
  the start time of each video/sound in the json file as well as add audio or video tracks.
* that said the .aaf file included was created for one video and one audio, however json file was updated after that.

* in simple words, just change the .json file to include your video and audio details and run the aaf_machine.py and it will create a .aaf file, 
  the data referenced must be in the same folder.
