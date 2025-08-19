import aaf2
import os

aaf_path = "new.aaf"
video_filename = "output.mxf"  # Change to MXF format
audio_filename = "output.wav"
base_name = os.path.splitext(os.path.basename(aaf_path))[0]

# Check if files exist and their sizes
print(f"Checking input files:")
if not os.path.exists(video_filename):
    print(f"ERROR: {video_filename} not found!")
    exit(1)
if not os.path.exists(audio_filename):
    print(f"ERROR: {audio_filename} not found!")
    exit(1)

print(f"Video file: {video_filename} ({os.path.getsize(video_filename)} bytes)")
print(f"Audio file: {audio_filename} ({os.path.getsize(audio_filename)} bytes)")
print()

try:
    with aaf2.open(aaf_path, 'w') as f:
        print("Creating AAF file...")
        
        # Set up file names with just the basename (no path)
        video_basename = os.path.basename(video_filename)
        audio_basename = os.path.basename(audio_filename)
        
        # creating mastermob for media, setting the name to video filename with extension
        mob = f.create.MasterMob(video_basename) # the mastermob contains the video
        a_mob = f.create.MasterMob(audio_basename) # the mastermob contains the audio data
        f.content.mobs.append(mob) # add the data to the AAF content
        f.content.mobs.append(a_mob) # add the audio data to the AAF content
        print("Created MasterMobs")
        
        edit_rate = 25

        # Use MXF import and create proper file locators
        print("Importing video from MXF...")
        # Create SourceMob for video
        video_source_mob = f.create.SourceMob(video_basename + ".PHYS")
        f.content.mobs.append(video_source_mob)
        
        # Create file locator for video
        video_locator = f.create.NetworkLocator()
        video_locator['URLString'].value = video_basename  # Just the filename
        
        # Create essence descriptor for MXF
        video_descriptor = f.create.CDCIDescriptor()
        video_descriptor['Locator'].append(video_locator)
        video_descriptor['SampleRate'].value = edit_rate
        video_descriptor['StoredWidth'].value = 1920
        video_descriptor['StoredHeight'].value = 1080
        video_descriptor['FrameLayout'].value = "FullFrame"
        video_descriptor['ImageAspectRatio'].value = "16/9"
        video_descriptor['Length'].value = 250  # 10 seconds at 25fps
        video_source_mob.descriptor = video_descriptor
        
        # Create video slot
        video_source_slot = video_source_mob.create_empty_slot(edit_rate=edit_rate, media_kind='picture', slot_id=1)
        video_source_slot.segment.length = 250
        
        # Link MasterMob to SourceMob
        mob_video_slot = mob.create_timeline_slot(edit_rate=edit_rate)
        mob_video_slot.segment = video_source_mob.create_source_clip(1, media_kind='picture')
        mob_video_slot.segment.length = 250
        print("Video linked successfully")
        
        print("Importing audio...")
        # Create SourceMob for audio
        audio_source_mob = f.create.SourceMob(audio_basename + ".PHYS")
        f.content.mobs.append(audio_source_mob)
        
        # Create file locator for audio
        audio_locator = f.create.NetworkLocator()
        audio_locator['URLString'].value = audio_basename  # Just the filename
        
        # Create essence descriptor for audio
        audio_descriptor = f.create.PCMDescriptor()
        audio_descriptor['Locator'].append(audio_locator)
        audio_descriptor['SampleRate'].value = 48000
        audio_descriptor['Channels'].value = 2
        audio_descriptor['QuantizationBits'].value = 16
        audio_descriptor['BlockAlign'].value = 4
        audio_descriptor['AverageBPS'].value = 192000
        audio_descriptor['AudioSamplingRate'].value = 48000
        audio_descriptor['Length'].value = 480000  # 10 seconds at 48kHz
        audio_source_mob.descriptor = audio_descriptor
        
        # Create audio slot
        audio_source_slot = audio_source_mob.create_empty_slot(edit_rate=edit_rate, media_kind='sound', slot_id=1)
        audio_source_slot.segment.length = 250  # 10 seconds in timeline frames
        
        # Link MasterMob to SourceMob
        mob_audio_slot = a_mob.create_timeline_slot(edit_rate=edit_rate)
        mob_audio_slot.segment = audio_source_mob.create_source_clip(1, media_kind='sound')
        mob_audio_slot.segment.length = 250
        print("Audio linked successfully")

        # setting the mob's name property to the basename only 
        mob.name = video_basename
        a_mob.name = audio_basename

        # Get video and audio slots from their respective MasterMobs
        print(f"Video slots: {len(mob.slots)}")
        print(f"Audio slots: {len(a_mob.slots)}")
        
        if len(mob.slots) == 0:
            print("ERROR: No video slots created!")
            exit(1)
        if len(a_mob.slots) == 0:
            print("ERROR: No audio slots created!")
            exit(1)
            
        video_slot = mob.slots[0]  # video slot from video MasterMob
        audio_slot = a_mob.slots[0]  # audio slot from audio MasterMob
        
        print(f"Video slot media_kind: {video_slot.media_kind}")
        print(f"Audio slot media_kind: {audio_slot.media_kind}")
        print(f"Video slot datadef: {video_slot.datadef}")
        print(f"Audio slot datadef: {audio_slot.datadef}")

        # Remove all existing CompositionMobs AFTER essence import
        for m in list(f.content.mobs):
            if m.__class__.__name__ == "CompositionMob":
                f.content.mobs.remove(m)

        # Create only one timeline (CompositionMob)
        comp_mob = f.create.CompositionMob("Timeline") 
        f.content.mobs.append(comp_mob)
        print("Created timeline")

        # Add video to timeline (slot_id=1)
        video_source_clip = f.create.SourceClip(
            length=video_slot.length,
            mob_id=mob.mob_id,
            slot_id=video_slot.slot_id,
            start=0
        )
        # Try using create_picture_slot without parameters then set properties
        video_timeline_slot = comp_mob.create_picture_slot(edit_rate=edit_rate)
        video_timeline_slot.slot_id = 1
        # Add SourceClip to the sequence instead of replacing the segment
        video_timeline_slot.segment.components.append(video_source_clip)
        print(f"Added video to timeline - media_kind: {video_timeline_slot.media_kind}")
        print("Added video to timeline")

        # Add audio to timeline (slot_id=2) - reference the audio MasterMob
        audio_source_clip = f.create.SourceClip(
            length=audio_slot.length,
            mob_id=a_mob.mob_id,  # Use audio MasterMob ID instead of video MasterMob
            slot_id=audio_slot.slot_id,
            start=0
        )
        # Try using create_sound_slot without parameters then set properties
        audio_timeline_slot = comp_mob.create_sound_slot(edit_rate=edit_rate)
        audio_timeline_slot.slot_id = 2
        # Add SourceClip to the sequence instead of replacing the segment
        audio_timeline_slot.segment.components.append(audio_source_clip)
        print(f"Added audio to timeline - media_kind: {audio_timeline_slot.media_kind}")
        print("Added audio to timeline")
        
        print("AAF file creation completed successfully!")
        
except Exception as e:
    print(f"ERROR during AAF creation: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print(f"Final AAF file size: {os.path.getsize(aaf_path)} bytes")