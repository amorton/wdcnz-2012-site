"""Controllers for page endpoints"""

import datetime
import os.path
import time

from mako import lookup as mako_lookup

import pycassa
from pycassa.cassandra import ttypes as cass_types

import tornado.web
from tornado import escape

from wdcnz import tasks

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# 

class ControllerBase(tornado.web.RequestHandler):
    
    template_lookup = mako_lookup.TemplateLookup(
        directories=["wdcnz/templates"], 
        module_directory='/tmp/mako_modules')

    # ========================================================================
    # Cassandra Helpers

    def column_family(self, name):
        return pycassa.ColumnFamily(self.application.cass_pool, name, 
            read_consistency_level=cass_types.ConsistencyLevel.QUORUM, 
            write_consistency_level=cass_types.ConsistencyLevel.QUORUM)

    # ========================================================================
    # RequestHandler overrides 
    
    def get_current_user(self):
        user_json = self.get_cookie("user")
        if not user_json:
            return {}
        return escape.json_decode(escape.url_unescape(user_json)) 

    # ========================================================================
    # Custom

    def _user_cookie(self, user):
        
        return escape.url_escape(escape.json_encode({
            k : v
            for k, v in user.iteritems()
            if k not in ["password"]
        }))


    def render(self, template_name, **kwargs):
        
        if "user" not in kwargs:
            kwargs["user"] = self.current_user

        template = self.template_lookup.get_template(template_name)
        self.write(template.render(**kwargs))
        return

    def next_tweet_id(self):
        """Returns a tuple of the current time stamp in isoformat 
        and the integer tweet_id to use.
        """
        now = time.time()
        return (
            datetime.datetime.fromtimestamp(now).isoformat(), 
            int(now * 10**6)
        )
        
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# 

class Home(ControllerBase):
    
    def get(self):
        
        user = self.current_user
        if not user:
            self.render("pages/splash.mako")
            return
        
        user_timeline_cf = self.column_family("UserTimeline")        
        row_key = self.current_user["user_name"]
        
        try:
            timeline_tweets = user_timeline_cf.get(row_key, column_count=20)
        except (pycassa.NotFoundException):
            timeline_tweets = {}

        tweets = [
            escape.json_decode(json)
            for json in timeline_tweets.values()
        ]
        self.render("pages/home.mako", tweets=tweets)
        return

class Tweet(ControllerBase):
    
    
    @tornado.web.authenticated
    def post(self):
        
        timestamp, tweet_id = self.next_tweet_id()
        tweet_body = self.get_argument("tweet_body")
        this_user = self.current_user["user_name"]
        
        user_tweets_cf = self.column_family("UserTweets")
        user_timeline_cf = self.column_family("UserTimeline")
        
        with pycassa.batch.Mutator(self.application.cass_pool) as batch:
            batch.write_consistency_level = cass_types.ConsistencyLevel.QUORUM
            
            # Store the tweet against the user
            row_key = this_user
            columns = {
                (tweet_id, "tweet_id")  : str(tweet_id),
                (tweet_id, "body"): tweet_body, 
                (tweet_id, "user_name") : self.current_user["user_name"], 
                (tweet_id, "timestamp") : timestamp
            }
            batch.insert(user_tweets_cf, row_key, columns)
            
            # Put the tweet into the users timeline
            row_key = self.current_user["user_name"]
            tweet_json = escape.json_encode({
                "tweet_id" : tweet_id,
                "body" : tweet_body, 
                "user_name" : this_user, 
                "timestamp" : timestamp
            })
            columns = {
                tweet_id : tweet_json
            }
            batch.insert(user_timeline_cf, row_key, columns)
        
        #
        tasks.deliver_tweet.delay(this_user, tweet_id, tweet_json)
        self.redirect("/")
        return

class User(ControllerBase):

    @tornado.web.authenticated
    def get(self, user_name):
        
        # Step 1 - get the user we want to display
        user_cf = self.column_family("User")
        row_key = user_name
        user = user_cf.get(row_key)
        
        # Step 2 - get all the tweets this user has posted
        user_timeline_cf = self.column_family("UserTweets")
        row_key = user_name

        try:
            raw_tweets = user_timeline_cf.get(row_key, column_count=20)
        except (pycassa.NotFoundException):
            raw_tweets = {}
            
        # These are composite columns 
        tweets = []
        this_tweet = {}
        last_tweet_id = None
        
        for col_name, col_value in raw_tweets.iteritems():
            this_tweet_id, tweet_property = col_name

            if last_tweet_id and (last_tweet_id != this_tweet_id):
                tweets.append(this_tweet)
                this_tweet = {}
            this_tweet[tweet_property] = col_value
        if this_tweet:
            tweets.append(this_tweet)
        
        # Step 3 - get the followers
        # OrderedFollowers
        # row_key is the user_name
        # column_name is the (timestamp, user_name)
        
        cf = self.column_family("OrderedFollowers")
        row_key = user_name
        
        try:
            follower_cols = cf.get(row_key, column_count=20)
        except (pycassa.NotFoundException):
            follower_cols = {}
        
        # We have the columns 
        # {(timestamp, user_name) : None}
        follower_names = [
            key[1]
            for key in follower_cols.keys()
        ]
        
        # Pivot to get the user data
        if follower_names:
            cf = self.column_family("User")
            users_cols = cf.multiget(follower_names)
            
            #have {row_key : {col_name : col_value}}
            followers = users_cols.values()
        else:
            followers = []
            
        # Step 3 - get who the user is following
        # OrderedFollowing
        # row_key is the user_name
        # column_name is the (timestamp, user_name)
        
        cf = self.column_family("OrderedFollowing")
        row_key = user_name
        
        try:
            following_cols = cf.get(row_key, column_count=20)
        except (pycassa.NotFoundException):
            following_cols = {}
        
        # We have the columns 
        # {(timestamp, user_name) : None}
        following_names = [
            key[1]
            for key in following_cols.keys()
        ]
        
        # Pivot to get the user data
        if following_names:
            cf = self.column_family("User")
            users_cols = cf.multiget(following_names)
            
            #have {row_key : {col_name : col_value}}
            following = users_cols.values()
        else:
            following = []
        
        # Step 4 - check if the current user is following this one.
        # AllFollowers CF 
        # row key is user_name
        # column_name is follower user_name
        
        cf = self.column_family("AllFollowers")
        row_key = user_name
        columns = [
            self.current_user["user_name"]
        ]
        
        try:
            is_following = True if cf.get(row_key, columns) else False
        except (pycassa.NotFoundException):
            is_following = False
        
        is_current_user = user_name == self.current_user["user_name"]
        
        self.render("pages/user.mako", tweets=tweets,
            followers=followers, following=following, 
            is_following=is_following, is_current_user=is_current_user)
        return

class UserFollowers(ControllerBase):

    @tornado.web.authenticated
    def post(self, user_to_follow):
        """Updates the logged in user to follow ``user_to_follow``."""
        
        this_user = self.current_user["user_name"]
        
        # Step 1 - check if we already folow user_to_follow
        all_followers_cf = self.column_family("AllFollowers")
        row_key = user_to_follow
        columns = [
            this_user
        ]
        
        try:
            existing = all_followers_cf.get(row_key, columns=columns)
        except (pycassa.NotFoundException):
            # not following the user. 
            pass
        else:
            # no double dipping. 
            self.redirect("/users/%(user_to_follow)s" % vars())
            return
            
        # Step 2 - lets get following 
        with pycassa.batch.Mutator(self.application.cass_pool) as batch:
            batch.write_consistency_level = cass_types.ConsistencyLevel.QUORUM
            
            now = int(time.time() * 10**6)
            
            # TODO: just use columns. 
            # OrderedFollowers CF stores who is following a user ordered by 
            # when they started.
            row_key = user_to_follow
            columns = {
                (now, this_user) : ""
            }
            batch.insert(self.column_family("OrderedFollowers"), row_key, 
                columns)
            
            # OrderedFollowing CF stores who a user is following ordered by 
            # when they started
            row_key = this_user
            columns = {
                (now, user_to_follow) : ""
            }
            batch.insert(self.column_family("OrderedFollowing"), row_key, 
                columns)

            # AllFollowers CF stores who is following a user without order
            row_key = user_to_follow
            columns = {
                this_user : ""
            }
            batch.insert(self.column_family("AllFollowers"), row_key, columns)

        self.redirect("/users/%(user_to_follow)s" % vars())
        return

class UserNotFollowers(ControllerBase):

    @tornado.web.authenticated
    def post(self, user_to_not_follow):
        """Updates the logged in user to not follow ``user_to_not_follow``."""
        
        raise RuntimeError("Not implemented")
        # this_user = self.current_user["user_name"]
        #       
        #       # Step 1 - check if we follow this user
        #       cf = self.column_family("AllFollowers")
        #       row_key = user_to_not_follow
        #       columns = [
        #           this_user
        #       ]
        #       
        #       try:
        #           existing = all_followers_cf.get(row_key, columns=columns)
        #       except (pycassa.NotFoundException):
        #           # not following the user. 
        #           self.redirect("/users/%(user_to_not_follow)s" % vars())
        #           return
        #       
        #       # Step 2 - stop following the user 
        #       with pycassa.batch.Mutator(self.application.cass_pool) as batch:
        #           batch.write_consistency_level = cass_types.ConsistencyLevel.QUORUM
        #           
        #           now = int(time.time() * 10**6)
        #           
        #           # TODO: just use columns. 
        #           # OrderedFollowers CF stores who is following a user ordered by 
        #           # when they started.
        #           row_key = user_to_follow
        #           columns = {
        #               (now, this_user) : ""
        #           }
        #           batch.insert(self.column_family("OrderedFollowers"), row_key, 
        #               columns)
        #           
        #           # OrderedFollowing CF stores who a user is following ordered by 
        #           # when they started
        #           row_key = this_user
        #           columns = {
        #               (now, user_to_follow) : ""
        #           }
        #           batch.insert(self.column_family("OrderedFollowing"), row_key, 
        #               columns)
        # 
        #           # AllFollowers CF stores who is following a user without order
        #           row_key = user_to_follow
        #           columns = {
        #               this_user : ""
        #           }
        #           batch.insert(self.column_family("AllFollowers"), row_key, columns)
        # 
        #       self.redirect("/users/%(user_to_follow)s" % vars())
        #       return
        
class Login(ControllerBase):
    
    def post(self):
        
        # new user signup
        user_name = self.get_argument("user_name")
        password = self.get_argument("user_password")
            
        user_cf = self.column_family("User")
        user_key = user_name
        try:
            user_cols = user_cf.get(user_key)
        except (cass_types.NotFoundException):
            msg = "Unknown user name." % vars()
            self.render("pages/splash.mako", error_message=msg)
            return
            
        if not password == user_cols["password"]:
            msg = "Invalid password." % vars()
            self.render("pages/splash.mako", error_message=msg)
            return
            
        self.set_cookie("user", self._user_cookie(user_cols))
        self.redirect("/")
        return
        
class Signup(ControllerBase):
    
    def post(self):
        
        # new user signup
        new_user_name = self.get_argument("new_user_name")
        new_user_password = self.get_argument("new_user_password")
        new_user_realname = self.get_argument("new_user_realname", 
            default=None)
            
        # Does this user exist ?
        user_cf = self.column_family("User")
        user_key = new_user_name
        try:
            user = user_cf.get(user_key)
        except (cass_types.NotFoundException):
            pass
        else:
            msg = "User name %(new_user_name)s is exists." % vars()
            self.render("pages/splash.mako", error_message=msg)
        
        # Nope, lets write this guy.
        user_cols = {
            "user_name" : new_user_name,
            "password" : new_user_password, 
        }
        # only store the real name if they gave us one. 
        if new_user_realname:
            user_cols["real_name"] = new_user_realname
        
        user_cf.insert(user_key, user_cols)
        self.set_cookie("user", self._user_cookie(user_cols))
        
        self.redirect("/")
        return

class Logout(ControllerBase):
    
    def get(self):
        
        self.clear_cookie("user")
        self.redirect("/")
        return
        