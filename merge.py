import aaf2

def wav_and_video_to_aaf(wav_path, video_path, aaf_path):
    with aaf2.open(aaf_path, 'w') as f:
        # Create Audio MasterMob and import audio
        audio_mob = f.create.MasterMob("Audio MasterMob")
        f.content.mobs.append(audio_mob)
        edit_rate = 48000
        audio_mob.import_audio_essence(wav_path, edit_rate)
        audio_slot = audio_mob.slots[0]

        # Create Video MasterMob (external reference only)
        video_mob = f.create.MasterMob("Video MasterMob")
        f.content.mobs.append(video_mob)
        video_edit_rate = 25  # typical video frame rate
        # No video essence import; just reference the MasterMob
        # Create a SourceClip referencing the video MasterMob
        video_slot_id = 1

        # Create CompositionMob (timeline)
        comp_mob = f.create.CompositionMob("Timeline")
        f.content.mobs.append(comp_mob)

        # Add video to timeline (slot_id=1)
        video_source_clip = f.create.SourceClip(
            length=audio_slot.length,  # match audio length for timeline
            mob_id=video_mob.mob_id,
            slot_id=1,
            start=0
        )
        video_timeline_slot = f.create.TimelineMobSlot(
            slot_id=1,
            segment=video_source_clip,
            edit_rate=video_edit_rate
        )
        comp_mob.slots.append(video_timeline_slot)

        # Add audio to timeline (slot_id=2)
        audio_source_clip = f.create.SourceClip(
            length=audio_slot.length,
            mob_id=audio_mob.mob_id,
            slot_id=audio_slot.slot_id,
            start=0
        )
        audio_timeline_slot = f.create.TimelineMobSlot(
            slot_id=2,
            segment=audio_source_clip,
            edit_rate=edit_rate
        )
        comp_mob.slots.append(audio_timeline_slot)

    print(f"AAF file created: {aaf_path}")

# Usage:
wav_and_video_to_aaf("output.wav", "output.mxf", "output.aaf")