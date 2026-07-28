

"""Get comments example: fetch and display threaded video comments."""



import sys

from pathlib import Path



if sys.platform == "win32":

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")



sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdk"))



from youtube_ai import YouTubeClient





def main():

    video_id = "dQw4w9WgXcQ"



    with YouTubeClient() as client:

        comments = client.get_comments(video_id, limit=10)



        print(f"Video:     {video_id}")

        print(f"Comments:  {len(comments['comments'])}")

        print()



        for comment in comments["comments"]:

            author = comment["author"]

            text = comment["text"][:120]

            likes = comment.get("likes", 0)

            replies = comment.get("reply_count", 0)

            verified = " (verified)" if comment.get("is_verified") else ""

            published = comment.get("published_time", "")



            print(f"  {author}{verified} - {published}")

            print(f"  {likes} likes, {replies} replies")

            print(f"  {text}")

            print()



        token = comments.get("continuation_token")

        if token:

            print("(More comments available via continuation token)")

            print()



            more = client.get_comments(video_id, limit=10, continuation_token=token)

            print(f"Next batch: {len(more['comments'])} comments")

            for comment in more["comments"][:5]:

                print(f"  {comment['author']}: {comment['text'][:80]}")





if __name__ == "__main__":

    main()
