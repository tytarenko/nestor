import logging
import requests

logger = logging.getLogger(__name__)


def get_avatar(backend, strategy, details, response, user=None, *args, **kwargs):
    logger.info(response)
    url = None
    if backend.name == 'facebook':
        url = 'http://graph.facebook.com/{}/picture?type=large'.format(response['id'])
    if backend.name == 'twitter':
        url = response.get('profile_image_url', '').replace('_normal', '')
    if backend.name == 'google-oauth2':
        url = response['image'].get('url')
        ext = url.split('.')[-1]
    if backend.name == 'vk-oauth2':
        url = get_vk_avatar(response['uid'])
    if url and not user.avatar_url:
        user.avatar_url = url
        user.save()


def get_vk_avatar(uid):
    url = 'https://api.vk.com/api.php?oauth=1&method=users.get&uids={}&fields=photo_400_orig'.format(uid)
    response = requests.get(url)
    if response.status_code == requests.codes.ok:
        return response.json()['response'][0]['photo_400_orig']
    return None

