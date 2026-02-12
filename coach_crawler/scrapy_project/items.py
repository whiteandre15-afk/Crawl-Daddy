import scrapy


class CoachItem(scrapy.Item):
    email = scrapy.Field()
    email_hash = scrapy.Field()
    first_name = scrapy.Field()
    last_name = scrapy.Field()
    full_name = scrapy.Field()
    title = scrapy.Field()
    role_category = scrapy.Field()
    sport = scrapy.Field()
    sport_normalized = scrapy.Field()
    school_id = scrapy.Field()
    school_name = scrapy.Field()
    level = scrapy.Field()
    sub_level = scrapy.Field()
    state = scrapy.Field()
    source_url = scrapy.Field()
    confidence_score = scrapy.Field()


class SchoolItem(scrapy.Item):
    name = scrapy.Field()
    slug = scrapy.Field()
    level = scrapy.Field()
    sub_level = scrapy.Field()
    division = scrapy.Field()
    conference = scrapy.Field()
    state = scrapy.Field()
    city = scrapy.Field()
    athletics_url = scrapy.Field()
    staff_directory_url = scrapy.Field()
    website_platform = scrapy.Field()
    organization_type = scrapy.Field()
