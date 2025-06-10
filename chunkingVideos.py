import os
import subprocess
import pandas as pd
from moviepy.video.io.VideoFileClip import VideoFileClip
#from moviepy import VideoFileClip
from sys import exit as e 

# Parse timeline and calculate side-view times
def parse_timeline(timeline_path):
    timeline = pd.read_excel(timeline_path)
    timeline["music_starttime_seconds"] = timeline["music_starttime"].apply(lambda x: int(x.split(":")[0]) * 60 + int(x.split(":")[1]))
    timeline["music_endtime_seconds"] = timeline["music_endtime"].apply(lambda x: int(x.split(":")[0]) * 60 + int(x.split(":")[1]))
    # timeline["side_view_start"] = timeline["music_starttime_seconds"] + sideview_offset_seconds
    # timeline["side_view_end"] = timeline["music_endtime_seconds"] + sideview_offset_seconds
    if "side_view_start" in timeline.columns:
        timeline["side_view_start"] = timeline["side_view_start"].apply(
            lambda x: int(x.replace("'", "").split(":")[0]) * 60 + int(x.replace("'", "").split(":")[1])
        )

    # Clean and convert "side_view_end" to seconds
    if "side_view_end" in timeline.columns:
        timeline["side_view_end"] = timeline["side_view_end"].apply(
            lambda x: int(x.replace("'", "").split(":")[0]) * 60 + int(x.replace("'", "").split(":")[1])
        )

    return timeline

def process_with_moviepy(video_path, start_seconds, end_seconds, clip_output_path):
    """Process the video using MoviePy"""
    video = VideoFileClip(video_path).subclip(start_seconds, end_seconds)
    video.write_videofile(clip_output_path, codec="libx264", audio_codec = get_audio_codec(video_path)
 ,
                          bitrate="5000k", preset="slow", threads=4)
    

def combine_videos(video_path, combined_filename="combination.mp4"):
    combined_file_path = os.path.join(video_path, combined_filename)

    # Check if the combined video already exists
    if os.path.exists(combined_file_path):
        print(combined_file_path)
        print(f"{combined_filename} already exists. Skipping combination.")
        return combined_file_path

    # Get the list of video files to combine
    video_files = sorted(
        [os.path.join(video_path, f) for f in os.listdir(video_path) if f.startswith("GH") and f.endswith(".MP4")],
        key=lambda x: int(os.path.basename(x)[2:4])  # Sort by GH01, GH02, etc.
    )
    if not video_files:
        print("No video files found to combine.")
        return None

    # Create a temporary text file listing all the video files
    list_file = os.path.join(video_path, "video_list.txt")
    with open(list_file, "w") as f:
        for video in video_files:
            f.write(f"file '{video}'\n")

    # Use ffmpeg to concatenate the videos without re-encoding
    ffmpeg_command = [
        "ffmpeg", "-f", "concat", "-safe", "0", "-i", list_file,
        "-c", "copy", combined_file_path  # Copy the original streams without re-encoding
    ]
    print("Combining videos into:", combined_file_path)
    result = subprocess.run(ffmpeg_command, capture_output=True, text=True)

    if result.returncode != 0:
        print("Error during video combination:", result.stderr)
    else:
        print(f"Videos combined successfully into {combined_file_path}.")

    # # Remove the temporary file list
    # os.remove(list_file)

    return combined_file_path


# # Extract video clips from the combined video

def extract_clips_from_combined_video(combined_file_path, timeline, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    timeline = timeline.iloc[12:]
    for _, row in timeline.iterrows():
        
        start_time = row["side_view_start"]
        end_time = row["side_view_end"]
        clip_label = row["File_name"] + ".mp4"
        
        output_file = os.path.join(output_dir, clip_label)

        print(f"Extracting {clip_label} from {start_time} to {end_time}...")
        ffmpeg_command = [
            "ffmpeg", "-ss", str(start_time), "-i", combined_file_path,  # Place -ss before -i for faster seek
            "-to", str(end_time - start_time),
            "-c:v", "libx264", "-c:a", "aac",
            "-preset", "slow", "-crf", "18", 
            output_file
        ]

        # Run the FFmpeg command and capture output
        result = subprocess.run(ffmpeg_command, capture_output=True, text=True)

        # Log success or failure
        if result.returncode == 0:
            print(f"Saved {clip_label} to {output_dir}.")
        else:
            print(f"Error extracting {clip_label}:")
            print(result.stderr)

        # Check if the file exists after extraction
        if not os.path.exists(output_file):
            print(f"Error: {output_file} not created.")
# # Main function
def main():
    # Define paths
    #sub_list ['968012','968038','968041','968043','968044','968045'] # list of patients ID
    sub_list = ['968038']
    #sub = '968012'
    # off_sets = {
    #     '968019':1,
    #     '968021': -20,
    #     '968022': 9,
    #     '968023': 10,
    #     '968024': 8,
    #     '968027': 9,
    #     '968030': -7,
    #     '968035': -4,
    #     '968037':11,
    #     '968038':-13,
    #     '968041':-3,
    #     '968043':6,
    #     '968044':-5,
    #     '968045':6,
    # }

    for sub in sub_list:
        video_path = f'/data/EmotionAssessmentProject/Pallab_Data/videos/OlderGroup/SideView/{sub}'
        timeline_path = f'/data/EmotionAssessmentProject/Pallab_Data/Timeline/{sub}_FrontView_Labels.xlsx'
        #output_dir = f'/data/EmotionAssessmentProject/Pallab_Data/clips/OlderGroup/SideView/{sub}'
        output_dir = f'/home/phong/Desktop/{sub}_side'
    # Start offset for side-view videos
        #sideview_offset_seconds = off_sets.get(sub, 0)  # Offset in seconds between side-view and front-view

    # Step 1: Combine the videos
        combined_file = combine_videos(video_path)
        if not combined_file:
            print("Failed to combine videos.")
            return

    # Step 2: Parse the timeline
        timeline = parse_timeline(timeline_path)
        print(timeline)

    # Step 3: Extract clips from the combined video
        extract_clips_from_combined_video(combined_file, timeline, output_dir)

if __name__ == "__main__":
    main()
