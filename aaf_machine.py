import aaf2
import os
import json

# function will take metadata from JSON file and aaf output name
def create_linked_aaf_from_metadata(metadata_file, aaf_output):
    # creating aaf file based on JSON metadat
    # Load metadata
    with open(metadata_file, 'r') as f:
        # the variable metadata will contain the data from JSON file
        metadata = json.load(f)
    
    timeline = metadata['timeline'] # get timeline data from json
    video_info = metadata['video'] # get video data from json
    video2_info = metadata['video2'] # get second video data from json
    audio_info = metadata['audio'] # get audio data from json
    tracks = metadata['tracks']
    
    print(f"Creating AAF: {aaf_output}")
    print(f"Timeline duration: {timeline['duration_seconds']}s ({timeline['total_frames']} frames)")
    print(f"Video 1: {video_info['duration_seconds']}s starting at {video_info['start_time_seconds']}s")
    print(f"Video 2: {video2_info['duration_seconds']}s starting at {video2_info['start_time_seconds']}s")
    print(f"Audio: {audio_info['duration_seconds']}s starting at {audio_info['start_time_seconds']}s")
    print()
    
    # Check if source files exist
    video_file = video_info['file']
    video2_file = video2_info['file']
    audio_file = audio_info['file']
    
    if not os.path.exists(video_file):
        print(f"ERROR: Video file {video_file} not found!")
        return False
    if not os.path.exists(video2_file):
        print(f"ERROR: Video 2 file {video2_file} not found!")
        return False
    if not os.path.exists(audio_file):
        print(f"ERROR: Audio file {audio_file} not found!")
        return False
    
    try:
        with aaf2.open(aaf_output, 'w') as f:
            edit_rate = timeline['edit_rate']
            
            # Create MasterMobs for both videos and audio
            video_master = f.create.MasterMob(video_info['basename'])
            video2_master = f.create.MasterMob(video2_info['basename'])
            audio_master = f.create.MasterMob(audio_info['basename'])
            f.content.mobs.append(video_master)
            f.content.mobs.append(video2_master)
            f.content.mobs.append(audio_master)
            print("Created MasterMobs for 2 videos and 1 audio")
            
            # Create external file references instead of importing essence
            print("Creating video file reference...")
            # Create SourceMob for video with file locator
            video_source_mob = f.create.SourceMob(video_info['basename'] + ".PHYS")
            f.content.mobs.append(video_source_mob)
            
            # Create file locator pointing to MXF file
            video_locator = f.create.NetworkLocator()
            video_locator['URLString'].value = video_info['basename']
            
            # Create video descriptor with file reference
            video_descriptor = f.create.CDCIDescriptor()
            video_descriptor['Locator'].append(video_locator)
            video_descriptor['SampleRate'].value = edit_rate
            video_descriptor['StoredWidth'].value = video_info['format']['width']
            video_descriptor['StoredHeight'].value = video_info['format']['height']
            video_descriptor['FrameLayout'].value = "FullFrame"
            video_descriptor['ImageAspectRatio'].value = video_info['format']['aspect_ratio']
            video_descriptor['Length'].value = video_info['duration_frames']
            # Add missing required properties
            video_descriptor['ComponentWidth'].value = 8  # 8-bit components
            video_descriptor['HorizontalSubsampling'].value = 2  # 4:2:2 subsampling typical for DNxHD
            video_descriptor['VideoLineMap'].value = [42, 0]  # Standard progressive line map
            video_source_mob.descriptor = video_descriptor
            
            # Create video slot in SourceMob
            video_source_slot = video_source_mob.create_empty_slot(edit_rate=edit_rate, media_kind='picture', slot_id=1)
            video_source_slot.segment.length = video_info['duration_frames']
            
            # Link MasterMob to SourceMob
            video_master_slot = video_master.create_timeline_slot(edit_rate=edit_rate)
            video_master_slot.segment = video_source_mob.create_source_clip(1, media_kind='picture')
            video_master_slot.segment.length = video_info['duration_frames']
            
            print("Creating video2 file reference...")
            # Create SourceMob for second video with file locator
            video2_source_mob = f.create.SourceMob(video2_info['basename'] + ".PHYS")
            f.content.mobs.append(video2_source_mob)
            
            # Create file locator pointing to second MXF file
            video2_locator = f.create.NetworkLocator()
            video2_locator['URLString'].value = video2_info['basename']
            
            # Create video2 descriptor with file reference
            video2_descriptor = f.create.CDCIDescriptor()
            video2_descriptor['Locator'].append(video2_locator)
            video2_descriptor['SampleRate'].value = edit_rate
            video2_descriptor['StoredWidth'].value = video2_info['format']['width']
            video2_descriptor['StoredHeight'].value = video2_info['format']['height']
            video2_descriptor['FrameLayout'].value = "FullFrame"
            video2_descriptor['ImageAspectRatio'].value = video2_info['format']['aspect_ratio']
            video2_descriptor['Length'].value = video2_info['duration_frames']
            # Add missing required properties
            video2_descriptor['ComponentWidth'].value = 8  # 8-bit components
            video2_descriptor['HorizontalSubsampling'].value = 2  # 4:2:2 subsampling typical for DNxHD
            video2_descriptor['VideoLineMap'].value = [42, 0]  # Standard progressive line map
            video2_source_mob.descriptor = video2_descriptor
            
            # Create video2 slot in SourceMob
            video2_source_slot = video2_source_mob.create_empty_slot(edit_rate=edit_rate, media_kind='picture', slot_id=1)
            video2_source_slot.segment.length = video2_info['duration_frames']
            
            # Link MasterMob to SourceMob for video2
            video2_master_slot = video2_master.create_timeline_slot(edit_rate=edit_rate)
            video2_master_slot.segment = video2_source_mob.create_source_clip(1, media_kind='picture')
            video2_master_slot.segment.length = video2_info['duration_frames']
            
            print("Creating audio file reference...")
            # Create SourceMob for audio with file locator
            audio_source_mob = f.create.SourceMob(audio_info['basename'] + ".PHYS")
            f.content.mobs.append(audio_source_mob)
            
            # Create file locator pointing to WAV file
            audio_locator = f.create.NetworkLocator()
            audio_locator['URLString'].value = audio_info['basename']
            
            # Create audio descriptor with file reference
            audio_descriptor = f.create.PCMDescriptor()
            audio_descriptor['Locator'].append(audio_locator)
            audio_descriptor['SampleRate'].value = audio_info['format']['sample_rate']
            audio_descriptor['Channels'].value = audio_info['format']['channels']
            audio_descriptor['QuantizationBits'].value = audio_info['format']['bit_depth']
            audio_descriptor['BlockAlign'].value = audio_info['format']['block_align']
            audio_descriptor['AverageBPS'].value = audio_info['format']['sample_rate'] * audio_info['format']['channels'] * (audio_info['format']['bit_depth'] // 8)
            audio_descriptor['AudioSamplingRate'].value = audio_info['format']['sample_rate']
            audio_descriptor['Length'].value = audio_info['format']['sample_rate'] * audio_info['duration_seconds']  # Total samples
            audio_source_mob.descriptor = audio_descriptor
            
            # Create audio slot in SourceMob
            audio_source_slot = audio_source_mob.create_empty_slot(edit_rate=edit_rate, media_kind='sound', slot_id=1)
            audio_source_slot.segment.length = audio_info['duration_frames']
            
            # Link MasterMob to SourceMob
            audio_master_slot = audio_master.create_timeline_slot(edit_rate=edit_rate)
            audio_master_slot.segment = audio_source_mob.create_source_clip(1, media_kind='sound')
            audio_master_slot.segment.length = audio_info['duration_frames']
            
            # Set names
            video_master.name = video_info['basename']
            video2_master.name = video2_info['basename']
            audio_master.name = audio_info['basename']
            
            # Get slots from MasterMobs
            video_slot = video_master.slots[0]
            video2_slot = video2_master.slots[0]
            audio_slot = audio_master.slots[0]
            
            print(f"Video 1 slot length: {video_slot.segment.length} frames")
            print(f"Video 2 slot length: {video2_slot.segment.length} frames")
            print(f"Audio slot length: {audio_slot.segment.length} frames")
            
            # Create timeline (CompositionMob)
            comp_mob = f.create.CompositionMob(timeline['name'])
            f.content.mobs.append(comp_mob)
            print("Created timeline")
            
            # Process video track with multiple clips
            video_track = tracks[0]
            
            # Create video timeline slot
            video_timeline_slot = comp_mob.create_picture_slot(edit_rate=edit_rate)
            video_timeline_slot.slot_id = video_track['track_id']
            
            # Process each video clip
            for i, video_clip_info in enumerate(video_track['clips']):
                print(f"Processing video clip {i+1}: {video_clip_info['source_file']}")
                
                # Determine which master mob to use based on source file
                if video_clip_info['source_file'] == video_info['basename']:
                    master_mob = video_master
                    master_slot = video_slot
                    print(f"Using video 1 master mob")
                elif video_clip_info['source_file'] == video2_info['basename']:
                    master_mob = video2_master
                    master_slot = video2_slot
                    print(f"Using video 2 master mob")
                else:
                    print(f"ERROR: Unknown video file {video_clip_info['source_file']}")
                    continue
                
                # Add filler if there's a gap before this clip
                if i == 0 and video_clip_info['timeline_in'] > 0:
                    # Add filler at the beginning
                    filler = f.create.Filler()
                    filler.length = video_clip_info['timeline_in']
                    filler.media_kind = 'Picture'
                    video_timeline_slot.segment.components.append(filler)
                    print(f"Added video filler: {video_clip_info['timeline_in']} frames")
                elif i > 0:
                    # Check if there's a gap between this clip and the previous one
                    prev_clip = video_track['clips'][i-1]
                    gap = video_clip_info['timeline_in'] - (prev_clip['timeline_out'] + 1)
                    if gap > 0:
                        filler = f.create.Filler()
                        filler.length = gap
                        filler.media_kind = 'Picture'
                        video_timeline_slot.segment.components.append(filler)
                        print(f"Added video gap filler: {gap} frames")
                
                # Create video source clip
                video_source_clip = f.create.SourceClip(
                    length=video_clip_info['duration'],
                    mob_id=master_mob.mob_id,
                    slot_id=master_slot.slot_id,
                    start=video_clip_info['source_in']  # Start position in source
                )
                
                # Add to sequence
                video_timeline_slot.segment.components.append(video_source_clip)
                print(f"Added video clip: {video_clip_info['duration']} frames at timeline position {video_clip_info['timeline_in']}")
            
            # Process audio track
            audio_track = tracks[1]
            audio_clip_info = audio_track['clips'][0]
            
            # Create audio timeline slot
            audio_timeline_slot = comp_mob.create_sound_slot(edit_rate=edit_rate)
            audio_timeline_slot.slot_id = audio_track['track_id']
            
            # For audio starting at 5 seconds, we need to add a filler first
            if audio_clip_info['timeline_in'] > 0:
                # Add filler for the gap before audio starts
                filler = f.create.Filler()
                filler.length = audio_clip_info['timeline_in']  # 125 frames (5 seconds)
                filler.media_kind = 'Sound'
                audio_timeline_slot.segment.components.append(filler)
                print(f"Added audio filler: {audio_clip_info['timeline_in']} frames")
            
            # Create audio source clip
            audio_source_clip = f.create.SourceClip(
                length=audio_clip_info['duration'],
                mob_id=audio_master.mob_id,
                slot_id=audio_slot.slot_id,
                start=audio_clip_info['source_in']  # Start position in source
            )
            
            # Add to sequence
            audio_timeline_slot.segment.components.append(audio_source_clip)
            print(f"Added audio clip: {audio_clip_info['duration']} frames at timeline position {audio_clip_info['timeline_in']}")
            
            print(f"Timeline structure:")
            print(f"  Video track: 0-{video_clip_info['timeline_out']} ({video_clip_info['duration']} frames)")
            print(f"  Audio track: {audio_clip_info['timeline_in']}-{audio_clip_info['timeline_out']} ({audio_clip_info['duration']} frames)")
            print(f"  Total duration: {timeline['total_frames']} frames ({timeline['duration_seconds']}s)")
            
            print("AAF file creation completed successfully!")
            return True
            
    except Exception as e:
        print(f"ERROR during AAF creation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    metadata_file = "timeline_metadata.json"
    aaf_output = "new.aaf"
    
    if create_linked_aaf_from_metadata(metadata_file, aaf_output):
        print(f"\\nFinal AAF file size: {os.path.getsize(aaf_output)} bytes")
        print(f"AAF file created: {aaf_output}")
        print(f"This AAF references to the metadata in json")
        print(f"Make sure these files are in the same directory when opening in DaVinci Resolve!")
    else:
        print("\\nAAF creation failed!")
