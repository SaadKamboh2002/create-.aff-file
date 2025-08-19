import aaf2
import os
import json

def create_linked_aaf_from_metadata(metadata_file, aaf_output):
    """Create a linked AAF file based on JSON metadata"""
    
    # Load metadata
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    timeline = metadata['timeline']
    video_info = metadata['video']
    audio_info = metadata['audio']
    tracks = metadata['tracks']
    
    print(f"Creating AAF: {aaf_output}")
    print(f"Timeline duration: {timeline['duration_seconds']}s ({timeline['total_frames']} frames)")
    print(f"Video: {video_info['duration_seconds']}s starting at {video_info['start_time_seconds']}s")
    print(f"Audio: {audio_info['duration_seconds']}s starting at {audio_info['start_time_seconds']}s")
    print()
    
    # Check if source files exist
    video_file = video_info['file']
    audio_file = audio_info['file']
    
    if not os.path.exists(video_file):
        print(f"ERROR: Video file {video_file} not found!")
        return False
    if not os.path.exists(audio_file):
        print(f"ERROR: Audio file {audio_file} not found!")
        return False
    
    try:
        with aaf2.open(aaf_output, 'w') as f:
            edit_rate = timeline['edit_rate']
            
            # Create MasterMobs for video and audio
            video_master = f.create.MasterMob(video_info['basename'])
            audio_master = f.create.MasterMob(audio_info['basename'])
            f.content.mobs.append(video_master)
            f.content.mobs.append(audio_master)
            print("Created MasterMobs")
            
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
            audio_master.name = audio_info['basename']
            
            # Get slots from MasterMobs
            video_slot = video_master.slots[0]
            audio_slot = audio_master.slots[0]
            
            print(f"Video slot length: {video_slot.segment.length} frames")
            print(f"Audio slot length: {audio_slot.segment.length} frames")
            
            # Create timeline (CompositionMob)
            comp_mob = f.create.CompositionMob(timeline['name'])
            f.content.mobs.append(comp_mob)
            print("Created timeline")
            
            # Process video track
            video_track = tracks[0]
            video_clip_info = video_track['clips'][0]
            
            # Create video timeline slot
            video_timeline_slot = comp_mob.create_picture_slot(edit_rate=edit_rate)
            video_timeline_slot.slot_id = video_track['track_id']
            
            # Create video source clip with specific timing
            video_source_clip = f.create.SourceClip(
                length=video_clip_info['duration'],
                mob_id=video_master.mob_id,
                slot_id=video_slot.slot_id,
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
        print(f"This AAF references: output.dnxhd, output.wav")
        print(f"Make sure these files are in the same directory when opening in DaVinci Resolve!")
    else:
        print("\\nAAF creation failed!")
