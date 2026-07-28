

"""Channel info example: get channel metadata and list uploaded videos."""



import sys

from pathlib import Path



if sys.platform == "win32":

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")



sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdk"))



from youtube_ai import YouTubeClient





def main():

    channel_id = "UCuAXFkgsw1L7xaCfnd5JJOw"



    with YouTubeClient() as client:

        info = client.get_channel_info(channel_id)



        print(f"Channel:     {info['title']}")

        print(f"Channel ID:  {info.get('channel_id') or channel_id}")

        print(f"Subscribers: {info['subscribers']}")

        print(f"Videos:      {info['video_count']}")

        print(f"Avatar:      {info['avatar']}")

        print()



        videos = client.get_channel_videos(channel_id, limit=10)



        print(f"Recent videos ({len(videos)} found):")

        for v in videos[:10]:

            print(f"  {v['title']}")

            print(f"    Duration: {v['duration']}  Views: {v['view_count_text']}  Published: {v['published']}")

            print()





if __name__ == "__main__":

    main()
