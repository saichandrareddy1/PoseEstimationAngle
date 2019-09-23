import subprocess

def convert_video(video_input, video_output):
    cmds = ['ffmpeg', '-i', video_input, video_output]
    print("DOne")
    subprocess.Popen(cmds)
    
