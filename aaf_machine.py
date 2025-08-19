import aaf2
import os
import json

# function will take metadata from JSON file and aaf output name
def create_linked_aaf_from_metadata(metadata_file, aaf_output):
    """Create a linked AAF file based on JSON metadata - handles any number of video/audio files"""
    
    # Load metadata
    with open(metadata_file, 'r') as f:
        # the variable metadata will contain the data from JSON file
        metadata = json.load(f)
    
    timeline = metadata['timeline'] # get timeline data from json
    tracks = metadata['tracks']
    
    # Automatically discover all media files in the JSON
    media_files = {}
    source_files = set()
    
    # Find all media entries (anything that's not 'timeline' or 'tracks')
    for key, value in metadata.items():
        if key not in ['timeline', 'tracks', 'description'] and isinstance(value, dict) and 'file' in value:
            media_files[value['basename']] = value
            source_files.add(value['file'])
            print(f"Found media: {key} -> {value['basename']}")
    
    print(f"Creating AAF: {aaf_output}")
    print(f"Timeline duration: {timeline['duration_seconds']}s ({timeline['total_frames']} frames)")
    print(f"Found {len(media_files)} media files:")
    for basename, info in media_files.items():
        print(f"  - {basename}: {info['duration_seconds']}s, {info['media_kind']}")
    print()
    
    # Check if all source files exist
    missing_files = []
    for file_path in source_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("ERROR: The following files were not found:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    try:
        with aaf2.open(aaf_output, 'w') as f:
            edit_rate = timeline['edit_rate']
            
            # Create MasterMobs and SourceMobs for all media files dynamically
            master_mobs = {}
            source_mobs = {}
            master_slots = {}
            
            print("Creating MasterMobs and SourceMobs for all media...")
            
            for basename, media_info in media_files.items():
                print(f"Processing {basename} ({media_info['media_kind']})...")
                
                # Create MasterMob
                master_mob = f.create.MasterMob(basename)
                f.content.mobs.append(master_mob)
                master_mob.name = basename
                master_mobs[basename] = master_mob
                
                # Create SourceMob
                source_mob = f.create.SourceMob(basename + ".PHYS")
                f.content.mobs.append(source_mob)
                source_mobs[basename] = source_mob
                
                # Create file locator
                locator = f.create.NetworkLocator()
                locator['URLString'].value = basename
                
                # Create appropriate descriptor based on media type
                if media_info['media_kind'] == 'picture':
                    # Video descriptor
                    descriptor = f.create.CDCIDescriptor()
                    descriptor['Locator'].append(locator)
                    descriptor['SampleRate'].value = edit_rate
                    descriptor['StoredWidth'].value = media_info['format']['width']
                    descriptor['StoredHeight'].value = media_info['format']['height']
                    descriptor['FrameLayout'].value = "FullFrame"
                    descriptor['ImageAspectRatio'].value = media_info['format']['aspect_ratio']
                    descriptor['Length'].value = media_info['duration_frames']
                    descriptor['ComponentWidth'].value = 8
                    descriptor['HorizontalSubsampling'].value = 2
                    descriptor['VideoLineMap'].value = [42, 0]
                    
                elif media_info['media_kind'] == 'sound':
                    # Audio descriptor
                    descriptor = f.create.PCMDescriptor()
                    descriptor['Locator'].append(locator)
                    descriptor['SampleRate'].value = media_info['format']['sample_rate']
                    descriptor['Channels'].value = media_info['format']['channels']
                    descriptor['QuantizationBits'].value = media_info['format']['bit_depth']
                    descriptor['BlockAlign'].value = media_info['format']['block_align']
                    descriptor['AverageBPS'].value = media_info['format']['sample_rate'] * media_info['format']['channels'] * (media_info['format']['bit_depth'] // 8)
                    descriptor['AudioSamplingRate'].value = media_info['format']['sample_rate']
                    descriptor['Length'].value = media_info['format']['sample_rate'] * media_info['duration_seconds']
                
                source_mob.descriptor = descriptor
                
                # Create slot in SourceMob
                source_slot = source_mob.create_empty_slot(edit_rate=edit_rate, media_kind=media_info['media_kind'], slot_id=1)
                source_slot.segment.length = media_info['duration_frames']
                
                # Create slot in MasterMob and link to SourceMob
                master_slot = master_mob.create_timeline_slot(edit_rate=edit_rate)
                master_slot.segment = source_mob.create_source_clip(1, media_kind=media_info['media_kind'])
                master_slot.segment.length = media_info['duration_frames']
                master_slots[basename] = master_slot
                
                print(f"Created {basename}: {media_info['duration_frames']} frames")
            
            print(f"Created {len(master_mobs)} MasterMobs and {len(source_mobs)} SourceMobs")
            
            # Create timeline (CompositionMob) - ONLY ONE
            comp_mob = f.create.CompositionMob(timeline['name'])
            f.content.mobs.append(comp_mob)
            print("Created single timeline")
            
            # Process all tracks dynamically
            for track in tracks:
                print(f"Processing {track['type']} track: {track['name']}")
                
                # Create appropriate timeline slot based on track type
                if track['type'] == 'video':
                    timeline_slot = comp_mob.create_picture_slot(edit_rate=edit_rate)
                    media_kind = 'Picture'
                elif track['type'] == 'audio':
                    timeline_slot = comp_mob.create_sound_slot(edit_rate=edit_rate)
                    media_kind = 'Sound'
                else:
                    print(f"Unknown track type: {track['type']}")
                    continue
                
                timeline_slot.slot_id = track['track_id']
                
                # Process all clips in this track
                for i, clip_info in enumerate(track['clips']):
                    source_file = clip_info['source_file']
                    print(f"  Processing clip {i+1}: {source_file}")
                    
                    # Find the corresponding master mob
                    master_mob = master_mobs.get(source_file)
                    master_slot = master_slots.get(source_file)
                    
                    if not master_mob or not master_slot:
                        print(f"ERROR: Could not find master mob for {source_file}")
                        continue
                    
                    # Add filler if there's a gap before this clip
                    if i == 0 and clip_info['timeline_in'] > 0:
                        # Add filler at the beginning
                        filler = f.create.Filler()
                        filler.length = clip_info['timeline_in']
                        filler.media_kind = media_kind
                        timeline_slot.segment.components.append(filler)
                        print(f"    Added filler: {clip_info['timeline_in']} frames")
                    elif i > 0:
                        # Check if there's a gap between this clip and the previous one
                        prev_clip = track['clips'][i-1]
                        gap = clip_info['timeline_in'] - (prev_clip['timeline_out'] + 1)
                        if gap > 0:
                            filler = f.create.Filler()
                            filler.length = gap
                            filler.media_kind = media_kind
                            timeline_slot.segment.components.append(filler)
                            print(f"    Added gap filler: {gap} frames")
                    
                    # Create source clip
                    source_clip = f.create.SourceClip(
                        length=clip_info['duration'],
                        mob_id=master_mob.mob_id,
                        slot_id=master_slot.slot_id,
                        start=clip_info['source_in']  # Start position in source
                    )
                    
                    # Add to sequence
                    timeline_slot.segment.components.append(source_clip)
                    print(f"    Added clip: {clip_info['duration']} frames at timeline position {clip_info['timeline_in']}")
            
            # Print final timeline structure
            print(f"\\nTimeline structure:")
            for track in tracks:
                print(f"  {track['name']} (Track {track['track_id']}):")
                for i, clip in enumerate(track['clips']):
                    print(f"    Clip {i+1}: {clip['source_file']} -> frames {clip['timeline_in']}-{clip['timeline_out']} ({clip['duration']} frames)")
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
