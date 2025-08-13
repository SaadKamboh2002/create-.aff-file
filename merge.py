import aaf2
import os

aaf_path = "output.aaf"
video_filename = "output.dnxhd"
audio_filename = "output.wav"
base_name = os.path.splitext(os.path.basename(aaf_path))[0]

with aaf2.open(aaf_path, 'w') as f:
    # Create MasterMob for media, set name to video filename (with extension)
    mob = f.create.MasterMob(video_filename)
    f.content.mobs.append(mob)

    edit_rate = 25

    # Import video and audio essence
    mob.import_dnxhd_essence(video_filename, edit_rate)
    mob.import_audio_essence(audio_filename, edit_rate)

    # Set the mob's name property to the full filename (for DaVinci compatibility)
    mob.name = video_filename

    # Get video and audio slots
    video_slot = mob.slots[0]  # assuming video is slot 0
    audio_slot = mob.slots[1]  # assuming audio is slot 1

    # Remove all existing CompositionMobs AFTER essence import
    for m in list(f.content.mobs):
        if m.__class__.__name__ == "CompositionMob":
            f.content.mobs.remove(m)

    # Create only one timeline (CompositionMob)
    comp_mob = f.create.CompositionMob("Timeline")
    f.content.mobs.append(comp_mob)

    # Add video to timeline (slot_id=1)
    video_source_clip = f.create.SourceClip(
        length=video_slot.length,
        mob_id=mob.mob_id,
        slot_id=video_slot.slot_id,
        start=0
    )
    video_timeline_slot = f.create.TimelineMobSlot(
        slot_id=1,
        segment=video_source_clip,
        edit_rate=edit_rate
    )
    comp_mob.slots.append(video_timeline_slot)

    # Add audio to timeline (slot_id=2)
    audio_source_clip = f.create.SourceClip(
        length=audio_slot.length,
        mob_id=mob.mob_id,
        slot_id=audio_slot.slot_id,
        start=0
    )
    audio_timeline_slot = f.create.TimelineMobSlot(
        slot_id=2,
        segment=audio_source_clip,
        edit_rate=edit_rate
    )
    comp_mob.slots.append(audio_timeline_slot)