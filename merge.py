import aaf2

def wav_to_aaf(wav_path, aaf_path):
    with aaf2.open(aaf_path, 'w') as f:
        # Create a MasterMob (top-level media object)
        mob = f.create.MasterMob("Audio MasterMob")
        f.content.mobs.append(mob)

        # Import WAV essence
        edit_rate = 48000  # common audio sample rate
        mob.import_audio_essence(wav_path, edit_rate)

        # Create a CompositionMob (timeline)
        comp_mob = f.create.CompositionMob("Audio Timeline")
        f.content.mobs.append(comp_mob)

        # Get the master audio slot
        master_slot = mob.slots[0]

        # Add a placeholder video slot (slot_id=1)
        # This creates an empty filler segment for video
        video_filler = f.create.Filler(length=master_slot.length)
        video_slot = f.create.TimelineMobSlot(
            slot_id=1,
            segment=video_filler,
            edit_rate=edit_rate
        )
        comp_mob.slots.append(video_slot)

        # Link CompositionMob to MasterMob's audio slot (slot_id=2)
        source_clip = f.create.SourceClip(
            length=master_slot.length,
            mob_id=mob.mob_id,
            slot_id=master_slot.slot_id,
            start=0
        )
        audio_slot = f.create.TimelineMobSlot(
            slot_id=2,
            segment=source_clip,
            edit_rate=edit_rate
        )
        comp_mob.slots.append(audio_slot)
    print(f"AAF file created: {aaf_path}")

wav_to_aaf("output.wav", "output.aaf")