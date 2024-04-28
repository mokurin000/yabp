import requests

from subprocess import call
from os import makedirs, path, remove
from bilibili_api import sync, Credential
from bilibili_api.search import search_by_type, SearchObjectType
from bilibili_api.video import Video

# （可选）认证信息，用于获取大于 360P 的视频。
# 参阅 https://nemo2011.github.io/bilibili-api/#/get-credential ，填入所需信息。
SESSDATA = ""
BILI_JCT = ""
BUVID3 = ""
DEDEUSERID = ""


def download_file(url, filename: str):
    with requests.get(
        url,
        stream=True,
        timeout=10,
        headers={
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
        },
    ) as r:
        r.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def download_dash(output_file: str, dash, bvid: str):
    """
    下载 DASH 格式视频
    """
    # 使用最好音质和第一个视频
    audio_url = max(dash["audio"], key=lambda a: a["bandwidth"])["base_url"]
    video_url = dash["video"][0]["base_url"]

    audio_file = f"temp/audio-{bvid}.m4s"
    video_file = f"temp/video-{bvid}.m4s"
    makedirs("temp", exist_ok=True)

    # 下载 DASH 音频和视频流
    download_file(audio_url, audio_file)
    download_file(video_url, video_file)

    # 合成视频
    call(
        [
            "ffmpeg.exe",
            "-i",
            audio_file,
            "-i",
            video_file,
            "-codec",
            "copy",
            output_file,
        ]
    )

    # 删除临时文件
    remove(audio_file)
    remove(video_file)


async def download_video(bvid: str) -> str:
    """
    从 bilibili 获取视频

    - bvid BV号
    - qn 视频清晰度

    详见 https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/docs/video/videostream_url.md#qn%E8%A7%86%E9%A2%91%E6%B8%85%E6%99%B0%E5%BA%A6%E6%A0%87%E8%AF%86

    返回视频保存到的路径
    """

    output_file = f"videos/{bvid}.mp4"
    if path.isfile(output_file):
        # 已下载的视频跳过重新下载
        return output_file

    credential = Credential(
        bili_jct=BILI_JCT, sessdata=SESSDATA, buvid3=BUVID3, dedeuserid=DEDEUSERID
    )
    video = Video(bvid=bvid, credential=credential)
    urls = await video.get_download_url(page_index=0, html5=True)
    makedirs("videos", exist_ok=True)

    if "dash" in urls:
        download_dash(output_file, urls["dash"], bvid)
    if "durl" in urls:
        durl = urls["durl"]
        max_quality = max(durl, key=lambda url: url["size"])["url"]
        download_file(max_quality, output_file)

    return output_file


async def search_videos(keyword: str) -> list[dict[str, str]]:
    """
    从 bilibili 搜索视频

    返回一个字典：
    - author 作者
    - bvid BV号
    - title 标题
    """
    videos = await search_by_type(
        keyword=keyword,
        search_type=SearchObjectType.VIDEO,
        debug_param_func=print,
    )
    return [
        {
            "author": video["author"],
            "bvid": video["bvid"],
            "title": video["title"],
        }
        for video in videos["result"]
    ]


async def main():
    videos = await search_videos("钟莉")
    video = videos[0]
    video_path = await download_video(video["bvid"])
    print(video_path)


if __name__ == "__main__":
    sync(main())
