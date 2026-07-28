

"""Basic search example: search YouTube and print results."""



import sys

from pathlib import Path



if sys.platform == "win32":

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")



sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdk"))



from youtube_ai import YouTubeClient





def main():

    with YouTubeClient() as client:

        results = client.search("python tutorial", limit=10)



        print(f"Found {results['count']} results\n")



        for item in results["results"]:

            if item["type"] == "video":

                print(f"  {item['title']}")

                print(f"  Channel: {item['channel']['name']}")

                print(f"  Duration: {item['duration']}")

                print(f"  Views: {item['view_count_text']}")

                print(f"  Published: {item['published']}")

                print(f"  URL: {item['url']}")

                print()



        if results["continuation_token"]:

            print("(More results available via continuation token)")





if __name__ == "__main__":

    main()
