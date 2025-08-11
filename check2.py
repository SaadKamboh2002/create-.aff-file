import opentimelineio as otio

def inspect_aaf(aaf_path):
    timeline = otio.adapters.read_from_file(aaf_path)
    print('Timeline name:', timeline.name)
    print('Tracks:')
    for track in timeline.tracks:
        print(f'  Track: {track.name} ({track.kind})')
        for clip in track:
            print(f'    Clip: {clip.name} - Duration: {clip.duration}')

if __name__ == "__main__":
    inspect_aaf("output.aaf")
