

"""Inspect download options and download one selected media variant.



Examples:

  python examples/download_video.py --inspect-only

  python examples/download_video.py --quality 720p

  python examples/download_video.py --mode video-only --quality 1080p

  python examples/download_video.py --mode audio-only

  python examples/download_video.py --quality 360p --start 30 --end 90



Bundled FFmpeg is used automatically for full video+audio output and clipping.

Pass --ffmpeg-path to use a specific executable.

"""



import argparse

import sys

from pathlib import Path



if sys.platform == "win32":

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")



sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdk"))



from youtube_ai import (

    DownloadMode,

    VideoQuality,

    YouTubeClient,

    download_video,

    get_download_options,

)





def parse_args():

    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("video_id", nargs="?", default="dQw4w9WgXcQ")

    parser.add_argument(

        "--quality",

        choices=[quality.value for quality in VideoQuality],

        default=VideoQuality.P144.value,

    )

    parser.add_argument(

        "--mode",

        choices=[mode.value for mode in DownloadMode],

        default=DownloadMode.FULL.value,

    )

    parser.add_argument("--start", type=float, default=None, help="Clip start in seconds")

    parser.add_argument("--end", type=float, default=None, help="Clip end in seconds")

    parser.add_argument("--output", default="./downloads")

    parser.add_argument("--ffmpeg-path", default=None, help="Optional FFmpeg executable path")

    parser.add_argument("--inspect-only", action="store_true")

    return parser.parse_args()





def main():

    args = parse_args()



    with YouTubeClient() as client:

        options = get_download_options(args.video_id, client=client, ffmpeg_path=args.ffmpeg_path)

        print(f"Title:      {options['title']}")

        print(f"Author:     {options['author']}")

        print(f"Duration:   {options['duration_seconds']}s")

        print(f"Qualities:  {options['available_qualities']}")

        print(f"Modes:      {options['supported_modes']}")

        print(f"ffmpeg:     {'available' if options['ffmpeg_available'] else 'missing'}")



        if args.inspect_only:

            return



        def on_progress(downloaded, total, percentage):

            completed_mb = downloaded / (1024 * 1024)

            total_mb = total / (1024 * 1024) if total else 0

            print(

                f"\r{percentage:3d}% ({completed_mb:.1f}/{total_mb:.1f} MiB)",

                end="",

            )



        path = download_video(

            args.video_id,

            quality=VideoQuality(args.quality),

            mode=DownloadMode(args.mode),

            start_time=args.start,

            end_time=args.end,

            output_path=Path(args.output),

            client=client,

            progress_callback=on_progress,

            ffmpeg_path=args.ffmpeg_path,

        )

        print(f"\nSaved to: {path}")





if __name__ == "__main__":

    main()
