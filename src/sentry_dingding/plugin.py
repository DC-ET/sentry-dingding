# coding: utf-8

import json

import requests
from sentry.plugins.bases.notify import NotificationPlugin

import sentry_dingding
from .forms import DingDingOptionsForm

DingTalk_API = "https://oapi.dingtalk.com/robot/send?access_token={token}"


class DingDingPlugin(NotificationPlugin):
    """
    Sentry plugin to send error counts to DingDing.
    """
    author = 'yjy'
    author_url = 'https://github.com/15058126273/sentry-dingding'
    version = sentry_dingding.VERSION
    description = 'Send error counts to DingDing.'
    resource_links = [
        ('Source', 'https://github.com/15058126273/sentry-dingding'),
        ('Bug Tracker', 'https://github.com/15058126273/sentry-dingding/issues'),
        ('README', 'https://github.com/15058126273/sentry-dingding/blob/master/README.md'),
    ]

    slug = 'DingDing'
    title = 'DingDing'
    conf_key = slug
    conf_title = title
    project_conf_form = DingDingOptionsForm

    def is_configured(self, project):
        """
        Check if plugin is configured.
        """
        return bool(self.get_option('access_token', project))

    def notify_users(self, group, event, *args, **kwargs):
        if not self.is_configured(group.project):
            return None
        if self.should_notify(group, event):
            self.post_process(group, event, *args, **kwargs)
        else:
            return None

    def findrepeatstart(self, origin, matchlen):
    	if matchlen < 2 or len(origin) <= matchlen:
    		return -1
    	i = origin.find(origin[0:matchlen], 1)
    	if i == -1:
    		return self.findrepeatstart(origin, matchlen // 2)
    	return i

    def findrepeatend(self, origin):
    	return origin.rfind("...")

    def cutrepeat(self, origin):
    	repeatstart = self.findrepeatstart(origin, 120)
    	if repeatstart == -1:
    		return origin
    	repeatend = self.findrepeatend(origin)
    	if (repeatend == -1):
    		return origin
    	return origin[0:repeatstart] + origin[repeatend:]

    def post_process(self, group, event, *args, **kwargs):
        """
        Process error.
        """
        if not self.is_configured(group.project):
            return

        if group.is_ignored():
            return

        access_token = self.get_option('access_token', group.project)
        send_url = DingTalk_API.format(token=access_token)
        title = u"New alert from {}".format(event.project.slug)
        message = self.cutrepeat(event.message)
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": u"#### {title} \n > {message} [href]({url})".format(
                    title=title,
                    message=message,
                    url=u"{}events/{}/".format(group.get_absolute_url(), event.id),
                )
            }
        }
        requests.post(
            url=send_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(data).encode("utf-8")
        )
