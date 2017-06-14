import time

from telegram.constants import MAX_FILESIZE_DOWNLOAD

from src.database import Database
from settings import BANNED_TAGS, IMAGES_PER_POST, IMAGES_FOR_LONG_POST, MAX_POST_AGE


def filter_posts(posts: list, db: Database):
    """
    :param posts: list of posts from Imgur
    :type posts: List[Dict[str, ...]]
    :type db: set
    :return: 
    Post: [
        {   
            is_album:   bool,
            is_dump:    bool,
            title:      str,
            desc:       str,
            topic:      str,
            tags:       [ str ],
            images_count: int,
            images:     [ Image ]
        }
    ]
    """
    filtered_posts = []

    for post in posts:
        post_id = post['id']
        if post_id in db:
            continue

        tags_list = [f'#{tag["name"]}' for tag in post['tags']]
        for bad_tag in BANNED_TAGS:
            if bad_tag in tags_list:
                continue

        new_post = build_new_post(post, tags_list)
        if new_post:
            filtered_posts.append(new_post)

    return filtered_posts


def build_new_post(post, tags_list):
    post_id = post['id']
    images_count = post['images_count'] if post['is_album'] else 1
    images = get_images(post)
    if images:
        return {
            'id': post_id,
            'is_album': post['is_album'],
            'is_dump': images_count > IMAGES_PER_POST,
            'title': post['title'],
            'desc': post['description'],
            'topic': post['topic'],
            'tags': tags_list,
            'datetime': post['datetime'],
            'images_count': images_count,
            'link': get_link(post, post_id),
            'images': images,
        }
    return None


def get_link(post, post_id):
    """
    if post is album:   'imgur.com/a/hurma'
    else:               'imgur.com/hurma'
    """
    addition = 'a/' if post['is_album'] else ''
    return 'https://imgur.com/' + addition + post_id


def get_images(post):
    formatted_images = []
    if post['is_album']:
        # long post will have only IMAGES_FOR_LONG_POST images in it
        # regular posts will have IMAGES_PER_POST images
        if post['images_count'] > IMAGES_PER_POST:
            images = post['images'][:IMAGES_FOR_LONG_POST]
        else:
            images = post['images'][:IMAGES_PER_POST]

        for image in images:
            formatted = format_image(image, post)
            if formatted:
                formatted_images.append(formatted)
    else:
        # if post is not album
        # then post IS the image/gif
        formatted = format_image(post, post)
        if formatted:
            formatted_images.append(formatted)
    return formatted_images


def format_image(image, post):
    """
    Image: {
        title:      str,
        desc:       str,
        animated:   bool,
        src:        str, link to mp4 if animated otherwise regular link
    }
    """
    now = time.time()
    if image['size'] < MAX_FILESIZE_DOWNLOAD and image['datetime'] + MAX_POST_AGE > now:
        return {
            'is_album': post['is_album'],
            'title': image['title'],
            'size': image['size'],
            "type": image['type'],  # image/png, image/jpeg, image/gif
            'desc': image['description'],
            'animated': image['animated'],
            'src': image['mp4'] if image['animated'] else image['link']
        }
    return None
