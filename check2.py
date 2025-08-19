import aaf2

def list_external_media_files(aaf_path):
    with aaf2.open(aaf_path, 'r') as f:
        media_files = set()
        for mob in f.content.mobs:
            print(f"Mob: {mob.name} ({mob.__class__.__name__})")
            for slot in mob.slots:
                segment = slot.segment
                # Recursively check segments for file locators
                def check_segment(seg):
                    # Essence descriptors often hold file references
                    if hasattr(seg, 'essence_descriptor') and seg.essence_descriptor:
                        desc = seg.essence_descriptor
                        # Look for file descriptors
                        if hasattr(desc, 'file_descriptor') and desc.file_descriptor:
                            fd = desc.file_descriptor
                            if hasattr(fd, 'name'):
                                media_files.add(fd.name)
                        # Some descriptors might directly have a path or locator
                        if hasattr(desc, 'path') and desc.path:
                            media_files.add(desc.path)
                    # Check if the segment itself has locators or file references
                    if hasattr(seg, 'file'):
                        media_files.add(seg.file)
                    # Check nested segments, like SourceClip segments or sequences
                    if hasattr(seg, 'segments'):
                        for s in seg.segments:
                            check_segment(s)
                
                check_segment(segment)

        if media_files:
            print("\nReferenced external media files:")
            for mf in media_files:
                print(f" - {mf}")
        else:
            print("No external media file references found in this AAF.")
            print('filename: ', aaf_path)

if __name__ == "__main__":
    aaf_file_path = "Timeline 1.aaf"
    list_external_media_files(aaf_file_path)
