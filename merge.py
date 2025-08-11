import aaf2

with aaf2.open("example2.aaf", 'w') as f:

    # objects are create with a factory
    # on the AAFFile Object
    mob = f.create.MasterMob("Demo2")

    # add the mob to the file
    f.content.mobs.append(mob)

    edit_rate = 25

    # lets also create a tape so we can add timecode (optional)
    tape_mob = f.create.SourceMob()
    f.content.mobs.append(tape_mob)

    timecode_rate = 25
    start_time = timecode_rate * 60 * 60 # 1 hour
    tape_name = "Demo Tape"

    # add tape slots to tape mob
    tape_mob.create_tape_slots(tape_name, edit_rate,
                               timecode_rate, media_kind='picture')

    # create sourceclip that references timecode
    tape_clip = tape_mob.create_source_clip(1, start_time)

    # now finally import the generated media
    mob.import_dnxhd_essence("output.dnxhd", edit_rate, tape_clip)
    mob.import_audio_essence("output.wav", edit_rate)

    # Add timeline (CompositionMob)
    video_slot = mob.slots[0]  # assuming video is slot 0
    audio_slot = mob.slots[1]  # assuming audio is slot 1

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