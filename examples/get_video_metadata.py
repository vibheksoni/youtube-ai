

"""Get video metadata example: fetch and display full video details."""



import sys

from pathlib import Path



if sys.platform == "win32":

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")



sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdk"))



from youtube_ai import YouTubeClient





def main():

    video_id = "dQw4w9WgXcQ"



    with YouTubeClient() as client:

        video = client.get_video(video_id)

        details = video["details"]



        print(f"Title:       {details['title']}")

        print(f"Author:      {details['author']}")

        print(f"Channel ID:  {details['channel_id']}")

        print(f"Duration:    {details['length_seconds']}s")

        print(f"Views:       {details['view_count']:,}")

        print(f"Likes:       {details.get('likes', 'N/A')}")

        print(f"Live:        {details['is_live']}")

        print(f"Private:     {details['is_private']}")

        print(f"Keywords:    {', '.join(details.get('keywords', []))}")

        print(f"Status:      {details['playability_status']}")

        print()



        print("Streaming formats (progressive):")

        for fmt in video["streaming_data"]["formats"]:

            print(f"  itag={fmt['itag']} {fmt['quality_label']} "

                  f"{fmt['mime_type']} {fmt.get('width', '')}x{fmt.get('height', '')}")

        print()



        print("Adaptive formats (first 5):")

        for fmt in video["streaming_data"]["adaptive_formats"][:5]:

            label = fmt.get("quality_label") or fmt.get("quality", "")

            print(f"  itag={fmt['itag']} {label} {fmt['mime_type']}")

        print()



        print(f"Caption tracks: {len(video['captions'])}")

        for cap in video["captions"]:

            kind = " (generated)" if cap["is_generated"] else ""

            print(f"  {cap['language_code']}: {cap['name']}{kind}")

        print()



        print(f"Related videos: {len(video['related_videos'])}")

        for related in video["related_videos"][:5]:

            print(f"  {related['title']}")





if __name__ == "__main__":

    main()
