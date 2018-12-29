class save_original_picture_info(object):
    def __init__(self, title, illust_id, author, date, browse, score, linkUrl, thumbnailUrl, originalUrl):
        self.title = title
        self.illust_id = illust_id
        self.author = author
        self.date = date
        self.browse = browse
        self.score = score
        self.linkUrl = linkUrl
        self.thumbnailUrl = thumbnailUrl
        self.originalUrl = originalUrl


    def print_attrs(self):
        print(
            'title:', self.title, ',',
            'illust_id:', self.illust_id, ',',
            'author:', self.illust_id, ',',
            'date:', self.date, ',',
            'browse:', self.browse, ',',
            'score:', self.score, ',',
            'linkUrl:', self.linkUrl, ',',
            'thumbnailUrl:', self.thumbnailUrl, ',',
            'originalUrl1:', self.originalUrl, ',',
        )