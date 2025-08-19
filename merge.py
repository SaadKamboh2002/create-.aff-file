import aaf2
import os

aaf_path = "output1.aaf"
video_filename = "output.dnxhd"
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
        
        # creating mastermob for media, setting the name to video filename with extension
        mob = f.create.MasterMob(video_filename) # the mastermob contains the video
        a_mob = f.create.MasterMob(audio_filename) # the mastermob contains the audio data
        f.content.mobs.append(mob) # add the data to the AAF content
        f.content.mobs.append(a_mob) # add the audio data to the AAF content
        print("Created MasterMobs")
        
        edit_rate = 25

        # Import video and audio essence using lower-level methods
        print("Creating video essence...")
        video_source_mob = f.create.SourceMob()
        video_source_mob.name = video_filename + ".PHYS"
        f.content.mobs.append(video_source_mob)
        
        # Create essence data for video
        video_essence_data = video_source_mob.create_essence(edit_rate, "picture", offline=False)
        with open(video_filename, 'rb') as video_file:
            video_essence_data.write(video_file.read())
        print("Video essence created and embedded")
        
        print("Creating audio essence...")
        audio_source_mob = f.create.SourceMob()
        audio_source_mob.name = audio_filename + ".PHYS"
        f.content.mobs.append(audio_source_mob)
        
        # Create essence data for audio
        audio_essence_data = audio_source_mob.create_essence(edit_rate, "sound", offline=False)
        with open(audio_filename, 'rb') as audio_file:
            audio_essence_data.write(audio_file.read())
        print("Audio essence created and embedded")
        
        # Link MasterMobs to SourceMobs
        mob.link_external_essence(video_source_mob)
        a_mob.link_external_essence(audio_source_mob)

        # setting the mob's name property to the full filename 
        mob.name = video_filename
        a_mob.name = audio_filename

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