#!/usr/bin/env python3
"""Render the 5-second Panovi source + result examples. Requires ffmpeg/ffprobe."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

SCENES = {
    'mountain': {
        'inputs': ('left-panovi_944A428E_C2362D.MOV', 'right-panovi_944A428E_30B6DB.MOV', 'panovi_A64BFC22.mp4'),
        'starts': (2 + 1 / 30, 2 + 3 / 30, 2.0),
    },
    'city': {
        'inputs': ('demo_left.MOV', 'demo_right.MOV', 'demo_stitched.mp4'),
        'starts': (0.5 + 1 / 30, 0.5 + 3 / 30, 0.5),
    },
}
DURATION = 5


def run(args):
    subprocess.run([str(a) for a in args], check=True)


def probe(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)
    ]))


def render(scene, source_dir, output_dir):
    cfg = SCENES[scene]
    inputs = [source_dir / name for name in cfg['inputs']]
    for path, start in zip(inputs, cfg['starts']):
        data = probe(path)
        video = next(s for s in data['streams'] if s['codec_type'] == 'video')
        if float(video.get('duration', data['format']['duration'])) < start + DURATION:
            raise ValueError(f'Too short for the selected range: {path}')
        if video.get('color_transfer') in ('arib-std-b67', 'smpte2084'):
            raise ValueError(f'Use the documented SDR source, not an HDR alternative: {path}')

    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='panovi-demo-') as tmp:
        clips = []
        # Decode and scale serially. This honors the mountain left camera's
        # -180-degree display matrix; never use -noautorotate here.
        for i, (path, start) in enumerate(zip(inputs, cfg['starts'])):
            clip = Path(tmp) / f'{i}.mkv'
            width = 400 if i < 2 else 1184
            run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-threads', '2',
                 '-ss', f'{start:.8f}', '-i', path, '-t', str(DURATION),
                 '-map', '0:v:0', '-an', '-sn', '-dn', '-map_metadata', '-1',
                 '-filter_threads', '1', '-vf',
                 f'fps=30,scale={width}:-2:flags=lanczos:out_color_matrix=bt709:out_range=tv,setsar=1,format=yuv420p',
                 '-c:v', 'ffv1', '-threads', '2', '-y', clip])
            clips.append(clip)

        output = output_dir / f'demo-{scene}.mp4'
        filters = (
            'color=c=0x0b0c2d:s=1280x840:r=30:d=5[bg];'
            '[0:v]pad=iw+4:ih+4:2:2:color=0x8ecdea[left];'
            '[1:v]pad=iw+4:ih+4:2:2:color=0x8ecdea[right];'
            '[2:v]pad=iw+4:ih+4:2:2:color=0x8ecdea[result];'
            '[bg][left]overlay=188:100:shortest=1[a];'
            '[a][right]overlay=688:100:shortest=1[b];'
            '[b][result]overlay=(W-w)/2:590-h/2:shortest=1,'
            'drawbox=x=624:y=208:w=32:h=6:color=0x8ecdea:t=fill,'
            'drawbox=x=637:y=195:w=6:h=32:color=0x8ecdea:t=fill,'
            'format=yuv420p[out]'
        )
        run(['ffmpeg', '-hide_banner', '-loglevel', 'error',
             '-threads', '1', '-i', clips[0], '-threads', '1', '-i', clips[1],
             '-threads', '1', '-i', clips[2], '-filter_complex_threads', '1',
             '-filter_complex', filters, '-map', '[out]', '-an', '-map_metadata', '-1',
             '-frames:v', '150', '-c:v', 'libx264', '-threads', '2',
             '-preset', 'medium', '-crf', '22', '-profile:v', 'high', '-level:v', '4.0',
             '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
             '-movflags', '+faststart', '-y', output])
        run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-threads', '2',
             '-ss', '2.5', '-i', output, '-frames:v', '1', '-q:v', '2',
             '-threads', '2', '-y', output_dir / f'demo-{scene}-poster.jpg'])

    data = probe(output)
    video = next(s for s in data['streams'] if s['codec_type'] == 'video')
    assert len(data['streams']) == 1, 'Expected video only; no audio/data tracks'
    assert video['codec_name'] == 'h264' and video['pix_fmt'] == 'yuv420p'
    assert (video['width'], video['height']) == (1280, 840)
    assert video['r_frame_rate'] == '30/1' and int(video['nb_frames']) == 150
    assert abs(float(data['format']['duration']) - DURATION) < 0.01
    print(f'{output}: 1280x840, 30fps, 5s, {int(data["format"]["size"]):,} bytes')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene', choices=['all', *SCENES], default='all')
    parser.add_argument('--mountain-dir', type=Path, default=Path.home() / 'Downloads/金時山DEMO候補')
    parser.add_argument('--city-dir', type=Path, default=Path(__file__).resolve().parents[2] / 'Panovi/Panovi/SampleVideos')
    parser.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parents[1] / 'img')
    args = parser.parse_args()
    for tool in ['ffmpeg', 'ffprobe']:
        if not shutil.which(tool):
            parser.error(f'{tool} is required')
    for scene in SCENES if args.scene == 'all' else [args.scene]:
        render(scene, getattr(args, f'{scene}_dir'), args.output_dir)


if __name__ == '__main__':
    main()
