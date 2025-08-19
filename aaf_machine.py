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
            
            # Import essence (linked, not embedded)
            print("Importing video essence...")
            video_master.import_dnxhd_essence(video_file, edit_rate)
            
            print("Importing audio essence...")
            audio_master.import_audio_essence(audio_file, edit_rate)
            
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
