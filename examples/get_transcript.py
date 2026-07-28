

"""Get transcript example: fetch and display video captions with timestamps."""



import sys

from pathlib import Path



if sys.platform == "win32":

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")



sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdk"))



from youtube_ai import YouTubeClient





def main():

    video_id = "dQw4w9WgXcQ"



    with YouTubeClient() as client:

        transcript = client.get_transcript(video_id, language_codes=("en",))



        print(f"Video:       {transcript['video_id']}")

        print(f"Language:    {transcript['language']} ({transcript['language_code']})")

        print(f"Generated:   {transcript['is_generated']}")

        print(f"Snippets:    {len(transcript['snippets'])}")

        print()



        print("Available tracks:")

        for track in transcript["available_tracks"]:

            kind = " (auto-generated)" if track["is_generated"] else ""

            print(f"  {track['language_code']}: {track['name']}{kind}")

        print()



        print("Transcript (first 20 lines):")

        for snippet in transcript["snippets"][:20]:

            mins = int(snippet["start"] // 60)

            secs = snippet["start"] % 60

            print(f"  [{mins:02d}:{secs:05.2f}] {snippet['text']}")





if __name__ == "__main__":

    main()
