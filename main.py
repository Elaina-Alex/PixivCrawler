import argparse
import json
import sys
import Image
from instance import *
from rich.progress import track
import PixivAPI
import complex_image


def update():
    download_test = False
    response = PixivAPI.get("https://raw.githubusercontent.com/Elaina-Alex/pixiv_crawler/main/update.json")
    if not os.path.exists('update.json'):
        json.dump(response, open('update.json', 'w'))
        download_test = True
    data = json.loads(open('update.json', 'r').read())
    if data['version'] < response['version']:
        print("检测到有新版本", response['version'], "是否进行更新？[yes/no]")
        choice = PixivAPI.input_str('>').strip()
        if choice == "yes":
            download_test = True
            print("开始更新", response['version'], "版本")
        else:
            download_test = False

    if download_test:
        with open(data['name'] + ".exe", 'wb') as file:
            print(response['download_url'].format(response['version']))
            file.write(PixivAPI.get(response['download_url'].format(response['version']), types="content"))
        print(data['name'] + ".exe", "下载完毕")
        json.dump(response, open('update.json', 'w'))
        print("三秒后自动退出脚本...")
        sys.exit()


def shell_author_works(author_id: str, next_url: str = ""):  # download author images save to local
    while True:
        if next_url is None:  # if next_url is None, it means that it is download complete
            return print("the end of author_works list")
        if next_url == "":  # if next_url is empty, it means it is the first time to download author works list
            response_list, next_url = PixivAPI.PixivApp.author_information(author_id=author_id)
        else:  # if next_url is not empty, it means it is the next time to download author works list
            response_list, next_url = PixivAPI.PixivApp.author_information(api_url=next_url)
        # if response_list is not list, it means that it is download complete
        multi_threading_image_pool: complex_image.Complex = complex_image.Complex()  # new threading pool
        if isinstance(response_list, list) and len(response_list) != 0:
            for illusts in response_list:  # add illusts to threading pool for download
                multi_threading_image_pool.add_image_info_obj(Image.ImageInfo(illusts))
            multi_threading_image_pool.start_download_threading()  # start download threading pool for download
        else:
            return print("get author works list error:", response_list)


@count_time
def shell_illustration(inputs):
    if len(inputs) >= 2:
        Vars.images_info = PixivAPI.PixivApp.images_information(PixivAPI.rec_id(inputs[1]))
        if isinstance(Vars.images_info, dict):
            Vars.images_info = Image.ImageInfo(Vars.images_info)
            Vars.images_info.show_images_information()
            if Vars.images_info.page_count == 1:
                Vars.images_info.save_image(Vars.images_info.original_url)
            else:
                Vars.images_info.save_image(Vars.images_info.original_url_list)
        else:
            print("没有找到相应的作品！")
    else:
        print("你没有输入id或者链接")


@count_time
def shell_search(inputs: list):
    if len(inputs) < 2:
        print("没有输入搜索信息")
        return False
    response_list = PixivAPI.Tag.search_information(png_name=inputs[1])
    if isinstance(response_list, list) and len(response_list) != 0:
        threading_image_pool = complex_image.Complex()
        for image_info in response_list:
            threading_image_pool.add_image_info_obj(Image.ImageInfo(image_info))
        threading_image_pool.start_download_threading()
    else:
        print("没有找到相应的作品！")


@count_time
def shell_download_follow_author():
    follow_information_list = PixivAPI.PixivApp.follow_information()
    if isinstance(follow_information_list, list):
        print("共有", len(follow_information_list), "个关注")
        for follow_information in follow_information_list:
            print("开始下载", follow_information['user']['name'], "的作品")
            threading_image_pool = complex_image.Complex()
            for illusts in follow_information['illusts']:
                threading_image_pool.add_image_info_obj(Image.ImageInfo(illusts))
            threading_image_pool.start_download_threading()
            print(follow_information['user']['name'], "的作品下载完毕")


@count_time
def shell_download_rank():
    response_list = PixivAPI.PixivApp.rank_information()
    if not isinstance(response_list, list):
        print("排行榜下载失败")
    elif len(response_list) == 0:
        print("排行榜获取完毕！")
    else:
        threading_image_pool = complex_image.Complex()
        for illusts in response_list:
            threading_image_pool.add_image_info_obj(Image.ImageInfo(illusts))
        threading_image_pool.start_download_threading()


@count_time
def shell_read_text_id():
    default_file_name = "pixiv_id_list.txt"
    if not os.path.exists(default_file_name):
        open(default_file_name, 'w').close()
    image_id_list = []
    for line in open(default_file_name, 'r', encoding='utf-8', newline="").readlines():
        if line.startswith("#") or line.strip() == "":
            continue
        image_id = re.findall(r'^(\d{1,8})', line)
        if image_id and len(image_id) >= 5:
            image_id_list.append(image_id[0])
    if isinstance(image_id_list, list) and len(image_id_list) != 0:
        threading_image_pool = complex_image.Complex()
        for image_id in track(image_id_list, description="本地插画集加载中..."):
            Vars.images_info = PixivAPI.PixivApp.images_information(image_id)
            if isinstance(Vars.images_info, dict):
                threading_image_pool.add_image_info_obj(Image.ImageInfo(Vars.images_info))
            else:
                return print("无法进行下载,ERROR:", Vars.images_info)
        threading_image_pool.start_download_threading()


def shell_test_pixiv_token():
    if Vars.cfg.data.get("refresh_token") == "":
        print("检测到本地档案没有令牌，请登入网站获取code来请求token，也可以将token自行写入本地档案")
        code_verifier = PixivAPI.login_pixiv.open_browser()
        if PixivAPI.login_pixiv.login(code_verifier, PixivAPI.input_str('code:').strip()):
            print(f"code信息验证成功！，token信息已经保存在本地档案，请继续使用")
        else:
            print(f"输入code无效，请重新尝试获取code！")
            shell_test_pixiv_token()
    if not PixivAPI.PixivApp.get_user_info(show_start=True):
        PixivAPI.refresh_pixiv_token()


def shell_download_recommend(next_url: str = ""):  # download recommend images from pixiv api and save to local
    while True:
        if next_url is None:  # if next_url is None, it means that it is download complete
            return print("the end of recommend list")
        if next_url == "":  # if next_url is empty, it means it is the first time to download recommend list
            response_list, next_url = PixivAPI.PixivApp.recommend_images()
        else:  # if next_url is not empty, it means it is the next time to download recommend list
            response_list, next_url = PixivAPI.PixivApp.recommend_images(api_url=next_url)

        # if response_list is not list, it means that it is download complete
        multi_threading_image_pool: complex_image.Complex = complex_image.Complex()  # new threading pool
        if isinstance(response_list, list) and len(response_list) != 0:
            for illusts in response_list:  # add illusts to threading pool for download
                multi_threading_image_pool.add_image_info_obj(Image.ImageInfo(illusts))
            multi_threading_image_pool.start_download_threading()  # start download threading pool for download
        else:
            return print("get recommend list error:", response_list)


def shell_download_stars(next_url: str = ""):  # get stars list and download all the images in the list
    while True:
        if next_url is None:
            return print("the end of stars list")  # if next_url is None, it means that it is download complete
        if next_url == "":  # if next_url is empty, it means it is the first time to download stars list
            response_list, next_url = PixivAPI.PixivApp.start_images()
        else:  # if next_url is not empty, it means it is the next time to download stars list
            response_list, next_url = PixivAPI.PixivApp.start_images(api_url=next_url)
        multi_threading_image_pool: complex_image.Complex = complex_image.Complex()  # new threading pool for download
        if isinstance(response_list, list) and len(response_list) != 0:
            for illusts in response_list:  # add illusts to threading pool for download
                multi_threading_image_pool.add_image_info_obj(Image.ImageInfo(illusts))
            multi_threading_image_pool.start_download_threading()  # start download threading pool for download
        else:
            return print("get star list error:", response_list)


def start_parser() -> argparse.Namespace:  # start parser for command line arguments and start download process
    parser = argparse.ArgumentParser()  # create parser object for command line arguments
    parser.add_argument(
        "-l", "--login",
        dest="login",
        default=False,
        action="store_true",
        help="登录账号"
    )  # add login argument to parser object for command line arguments
    parser.add_argument(
        "-d",
        "--download",
        dest="downloadbook",
        nargs=1,
        default=None,
        help="输入image-id"
    )  # add download argument to parser object for command line arguments for download image
    parser.add_argument(
        "-m", "--max",
        dest="threading_max",
        default=None,
        help="更改线程"
    )  # add max argument to parser object for command line arguments for change threading max
    parser.add_argument(
        "-n", "--name",
        dest="name",
        nargs=1,
        default=None,
        help="输入搜搜信息"
    )  # add name argument to parser object for command line arguments for search
    parser.add_argument(
        "-u",
        "--update",
        dest="update",
        default=False,
        action="store_true",
        help="下载本地档案"
    )  # add update argument to parser object for command line arguments for download local file
    parser.add_argument(
        "-s", "--stars",
        dest="stars",
        default=False,
        action="store_true",
        help="下载收藏插画"
    )  # add stars argument to parser object for command line arguments for download stars
    parser.add_argument(
        "-r", "--recommend",
        dest="recommend",
        default=False,
        action="store_true",
        help="下载推荐插画"
    )  # add recommend argument to parser object for command line arguments for download recommend
    parser.add_argument(
        "-k", "--ranking",
        dest="ranking",
        default=False,
        action="store_true",
        help="下载排行榜插画"
    )  # add ranking argument to parser object for command line arguments for download ranking
    parser.add_argument(
        "-c",
        "--clear_cache",
        dest="clear_cache",
        default=False,
        action="store_true"
    )  # add clear_cache argument to parser object for command line arguments for clear cache
    parser.add_argument(
        "-a",
        "--author",
        dest="author",
        nargs=1,
        default=None,
        help="输入作者-id"
    )  # add author argument to parser object for command line arguments for download author
    return parser.parse_args()  # return parser object for command line arguments and return it as a tuple


def shell_parser():
    args, shell_console = start_parser(), False
    if args.recommend:
        shell_download_recommend()
        shell_console = True

    if args.ranking:
        shell_download_rank()
        shell_console = True

    if args.stars:
        shell_download_stars()
        shell_console = True

    if args.update:
        shell_read_text_id()
        shell_console = True

    if args.clear_cache:
        Vars.cfg.data.clear(), set_config()
        Vars.cfg.save()
        sys.exit(3)

    if args.threading_max:
        Vars.cfg.data['max_thread'] = int(args.max)

    if args.name:
        shell_search(['n'] + args.name)
        shell_console = True

    if args.downloadbook:
        shell_illustration(['d'] + args.downloadbook)
        shell_console = True

    if args.author:
        shell_author_works(args.author[0])
        shell_console = True

    if args.login:
        shell_test_pixiv_token()
        shell_console = True

    if not shell_console:
        for info in Msg.msg_help:
            print('[帮助]', info)
        while True:
            shell(re.split('\\s+', PixivAPI.input_str('>').strip()))


def shell(inputs: list):
    if inputs[0] == 'q' or inputs[0] == 'quit':
        sys.exit("已退出程序")
    elif inputs[0] == 'h' or inputs[0] == 'help':
        for msg_help in Msg.msg_help:
            print('[帮助]', msg_help)
    elif inputs[0] == 'l' or inputs[0] == 'login':
        shell_test_pixiv_token()
    elif inputs[0] == 'd' or inputs[0] == 'download':
        shell_illustration(inputs)
    elif inputs[0] == 's' or inputs[0] == 'stars':
        shell_download_stars()
    elif inputs[0] == 'n' or inputs[0] == 'name':
        shell_search(inputs)
    elif inputs[0] == 't' or inputs[0] == 'recommend':
        shell_download_recommend()
    elif inputs[0] == 'u' or inputs[0] == 'update':
        shell_read_text_id(inputs)
    elif inputs[0] == 'r' or inputs[0] == 'rank':
        shell_download_rank()
    elif inputs[0] == 'f' or inputs[0] == 'follow':
        shell_download_follow_author()
    else:
        print(inputs[0], "为无效指令")


if __name__ == '__main__':
    set_config()
    # update()
    try:
        shell_test_pixiv_token()
        shell_parser()
    except KeyboardInterrupt:
        print("已手动退出程序")
        sys.exit(1)
    except Exception as error:
        print("程序意外退出，ERROR:", error)
