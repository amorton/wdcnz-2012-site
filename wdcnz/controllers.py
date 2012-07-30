"""Controllers for page endpoints"""

import datetime
import os.path
import time

from mako import lookup as mako_lookup

import pycassa
from pycassa.cassandra import ttypes as cass_types

import tornado.web
from tornado import escape

from wdcnz import tasks, util

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# 

class ControllerBase(tornado.web.RequestHandler):
    
    template_lookup = mako_lookup.TemplateLookup(
        directories=["wdcnz/templates"], 
        module_directory='/tmp/mako_modules')

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
        if "util" not in kwargs:
            kwargs["util"] = util
            
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
    
    def join_relation_users(self, rel_row, users):
        """Joins the data in the OrderedRelation row ``rel_row`` with the 
        ``users``. 
        
        ``rel_row`` is {(timestamp, user_name) : None}
        
        ``users`` is {user_name : {}}
        
        Returns a list of users. 
        """
        
        return [
            users[user_name]
            for timestamp, user_name in rel_row.keys()
            if user_name in users
        ]
        
    # ========================================================================
    # Cassandra Helpers

    def column_family(self, name):
        return pycassa.ColumnFamily(self.application.cass_pool, name, 
            read_consistency_level=cass_types.ConsistencyLevel.QUORUM, 
            write_consistency_level=cass_types.ConsistencyLevel.QUORUM)
            
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# 

class Signup(ControllerBase):
    
    def post(self):
        """Register the user."""
    
        user_name = self.get_argument("user_name").strip()
        password = self.get_argument("password").strip()
        # real name is optional
        real_name = self.get_argument("real_name", default="").strip()
        
        user_cf = self.column_family("User")
        
        # Does this user exist ?
        row_key = user_name
        
        try:
            # Get all the columns for the user.
            user = user_cf.get(row_key)
        except (pycassa.NotFoundException):
            pass
        else:
            msg = "User name %(user_name)s is exists." % vars()
            self.render("pages/splash.mako", error_message=msg)
            return
        
        # Add the new user to the Users CF
        columns = {
            "user_name" : user_name,
            "password" : password, 
        }
        # only store the real name if they gave us one. 
        if real_name:
            columns["real_name"] = real_name
        
        user_cf.insert(row_key, columns)
        self.set_cookie("user", self._user_cookie(columns))
        self.redirect("/")
        return


class Tweets(ControllerBase):
    
    @tornado.web.authenticated
    def post(self):
        "Post a tweet."
        
        timestamp, tweet_id = self.next_tweet_id()
        tweet_body = self.get_argument("tweet_body")
        this_user = self.current_user["user_name"]
        
        # Reference Column Families
        tweet_cf = self.column_family("Tweet")
        user_tweets_cf = self.column_family("UserTweets")
        user_timeline_cf = self.column_family("UserTimeline")
        global_timeline_cf = self.column_family("GlobalTimeline")
        user_metrics_cf = self.column_family("UserMetrics")
        
        with pycassa.batch.Mutator(self.application.cass_pool) as batch:
            batch.write_consistency_level = cass_types.ConsistencyLevel.QUORUM
            
            # Store the tweet in Tweet CF
            row_key = tweet_id
            columns = {
                "tweet_id"  : str(tweet_id),
                "body": tweet_body, 
                "user_name" : this_user, 
                "timestamp" : timestamp
            }
            batch.insert(tweet_cf, row_key, columns)
            
            # Store the tweet in UserTweets CF
            # This is a reference to the Tweet CF
            row_key = this_user
            columns = {
                tweet_id : ""
            }
            batch.insert(user_tweets_cf, row_key, columns)
            
            # Store the tweet in UserTimeline CF
            # This is a copy of the Tweet data.
            row_key = this_user
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
            
            # Store the tweet in GlobalTimeline CF
            # This is a reference to the Tweet CF
            row_key = datetime.date.today().isoformat()
            columns = {
                (tweet_id, this_user) : ""
            }
            batch.insert(global_timeline_cf, row_key, columns)
        
        #Exit batch context
        
        # Update count of the number of tweets.
        row_key = this_user
        user_metrics_cf.add(row_key, "tweets", value=1)
        
        # Deliver to Followers
        tasks.deliver_tweet.delay(this_user, tweet_id, tweet_json)
        
        self.redirect("/")
        return


class Home(ControllerBase):
    
    def get(self):
        """Show user timeline"""
        
        # Ensure logged in
        user = self.current_user
        if not user:
            self.render("pages/splash.mako")
            return
        
        # Reference CFs
        user_timeline_cf = self.column_family("UserTimeline")
        global_timeline_cf = self.column_family("GlobalTimeline")
        tweet_cf = self.column_family("Tweet")
        
        # Read tweets from UserTimeline CF
        row_key = self.current_user["user_name"]
        global_timeline = False
        
        try:
            user_timeline_cols = user_timeline_cf.get(row_key,column_count=20)
            # Have a dict of {tweet_id : tweet_json}
            tweets = [
                escape.json_decode(json)
                for json in user_timeline_cols.values()
            ]
        except (pycassa.NotFoundException):
            tweets = []
        
        # If no tweets in the users timeline check the global timeline
        if not tweets:
            
            row_key = datetime.date.today().isoformat()
            try:
                global_timeline_cols = global_timeline_cf.get(row_key, 
                    column_count=20)
            except (pycassa.NotFoundException):
                global_timeline_cols = {}
            
            if global_timeline_cols:
                # Have a dict of {(tweet_id, user_name) : none}
                # Need to make another request to get the tweet details
                
                row_keys = [
                    tweet_id
                    for tweet_id, user_name in global_timeline_cols.keys()
                ]
                
                tweet_cols = tweet_cf.multiget(row_keys)
                
                # Have {tweet_id : { property : value}}
                tweets = tweet_cols.values()
                global_timeline = True
        
        self.render("pages/home.mako", tweets=tweets, 
            global_timeline=global_timeline)
        return


class UserFollowers(ControllerBase):
    
    @tornado.web.authenticated
    def post(self, user_to_follow):
        """Starts the logged in user following ``user_to_follow``."""
        
        this_user = self.current_user["user_name"]
        
        # Reference CF's
        relationships_cf = self.column_family("Relationships")
        ordered_rels_cf = self.column_family("OrderedRelationships")
        user_metrics_cf = self.column_family("UserMetrics")
        
        # check if we already folow user_to_follow  
        row_key = (this_user, "following")
        columns = [
            user_to_follow
        ]
        try:
            existing = relationships_cf.get(row_key, columns=columns)
        except (pycassa.NotFoundException):
            # not following the user. 
            pass
        else:
            self.redirect("/users/%(user_to_follow)s" % vars())
            return
        
        with pycassa.batch.Mutator(self.application.cass_pool) as batch:
            batch.write_consistency_level = cass_types.ConsistencyLevel.QUORUM
            
            timestamp = int(time.time() * 10**6)
            
            # Store in Relationships CF
            row_key = (this_user, "following")
            columns = {
                user_to_follow : timestamp
            }
            batch.insert(relationships_cf, row_key, columns)
            
            row_key = (user_to_follow, "followers")
            columns = {
                this_user : timestamp
            }
            batch.insert(relationships_cf, row_key, columns)
            
            # Store in OrderedRelationships CF
            row_key = (this_user, "following")
            columns = {
                (timestamp, user_to_follow) : ""
            }
            batch.insert(ordered_rels_cf, row_key, columns)
            
            row_key = (user_to_follow, "followers")
            columns = {
                (timestamp, this_user) : ""
            }
            batch.insert(ordered_rels_cf, row_key, columns)
        # Exit batch
        
        # Update the metrics
        row_key = user_to_follow
        user_metrics_cf.add(row_key, "followers", value=1)
        
        row_key = this_user
        user_metrics_cf.add(row_key, "following", value=1)
        
        self.redirect("/users/%(user_to_follow)s" % vars())
        return


class DeletedTweets(ControllerBase):
    
    @tornado.web.authenticated
    def post(self):
        "Delete a tweet."
        
        tweet_id = int(self.get_argument("tweet_id"))
        this_user = self.current_user["user_name"]
        
        # Reference CFs
        tweet_cf = self.column_family("Tweet")
        user_tweets_cf = self.column_family("UserTweets")
        user_metrics_cf = self.column_family("UserMetrics")
        user_timeline_cf = self.column_family("UserTimeline")
        global_timeline_cf = self.column_family("GlobalTimeline")
        
        # Check the current user posted this tweet
        tweet = tweet_cf.get(tweet_id)
        if not tweet["user_name"] == this_user:
            raise tornado.web.HTTPError(401)
        
        with pycassa.batch.Mutator(self.application.cass_pool) as batch:
            batch.write_consistency_level = cass_types.ConsistencyLevel.QUORUM
            
            # Delete the tweet row from the Tweet CF
            row_key = tweet_id
            batch.remove(tweet_cf, row_key)
            
            # Delete the column that references the tweet in UserTweets CF
            row_key = this_user
            columns = [
                tweet_id,
            ]
            batch.remove(user_tweets_cf, row_key, columns)
            
            # Delete the copy of the tweet from the UserTimeline CF
            row_key = this_user
            columns = [
                tweet_id,
            ]
            batch.remove(user_timeline_cf, row_key, columns)
            
            # Delete the column that references the tweet in GlobalTimeline CF
            # row key is the day the tweet was posted
            row_key, _ = tweet["timestamp"].split("T", 1)
            columns = [
                (tweet_id, this_user)
            ]
            batch.remove(global_timeline_cf, row_key, columns)
        
        #Exit batch context
        
        # Update count of the number of tweets.
        row_key = this_user
        user_metrics_cf.add(row_key, "tweets", value=-1)
        
        # Recall from Followers
        tasks.recall_tweet.delay(tweet_id)
        
        self.redirect("/")
        return


class User(ControllerBase):
    
    @tornado.web.authenticated
    def get(self, user_name):
        
        user_cf = self.column_family("User")
        user_tweets_cf = self.column_family("UserTweets")
        user_metrics_cf = self.column_family("UserMetrics")
        tweet_cf = self.column_family("Tweet")
        ordered_rels_cf = self.column_family("OrderedRelationships")
        relationships_cf = self.column_family("Relationships")
        
        # get the user we want to display
        row_key = user_name
        user = user_cf.get(row_key)
        
        # get the user metrics
        row_key = user_name
        user_metrics = user_metrics_cf.get(row_key)
        
        #  get the tweets this user has posted
        row_key = user_name
        try:
            user_timeline_cols = user_tweets_cf.get(row_key, column_count=50)
        except (pycassa.NotFoundException):
            user_timeline_cols = {}
            
        # Have {tweet_id : None}
        # Make a second call to get the actual tweets
        if user_timeline_cols:
            row_keys = user_timeline_cols.keys()
            tweet_cols = tweet_cf.multiget(row_keys)
            
            # Have {tweet_id : {tweet_property : value}} 
            tweets = tweet_cols.values()
        else:
            tweets = []
        
        # get the 20 most recent followers and following relationships. 
        row_keys = [
            (user_name, "followers"), 
            (user_name, "following")
        ]
        rel_rows = ordered_rels_cf.multiget(row_keys, column_count=20)
        
        # Have { (user, relationship) : {(timestamp, other_user) : None}}
        # Call to get all other_user details
        row_keys = set()
        for rel_row in rel_rows.values():
            # Have {(timestamp, other_user) : None}
            row_keys.update(
                other_user
                for timestamp, other_user in rel_row.keys()
            )
        user_rows = user_cf.multiget(row_keys)
        
        followers = self.join_relation_users(
            rel_rows.get( (user_name, "followers"), {}), 
            user_rows)
        
        following = self.join_relation_users(
            rel_rows.get( (user_name, "following"), {}), 
            user_rows)
        
        # Check if these users follow each other.
        row_keys = [
            (user_name, "following"), 
            (user_name, "followers")
        ]
        columns = [
            self.current_user["user_name"]
        ]
        try:
            following_rows = relationships_cf.multiget(row_keys, 
                columns=columns)
        except (pycassa.NotFoundException):
            following_rows = {}
        
        # Have { (user_name, relationship) : {other_user : None}}
        follows_this_user = bool(following_rows.get((user_name, "following")))
        this_user_follows = bool(following_rows.get((user_name, "followers")))
        
        is_current_user = user_name == self.current_user["user_name"]
        
        self.render("pages/user.mako", 
            show_user=user, user_metrics=user_metrics,
            tweets=tweets,
            followers=followers, following=following, 
            follows_this_user=follows_this_user, 
            this_user_follows=this_user_follows, 
            is_current_user=is_current_user)
        return


class UserNotFollowers(ControllerBase):
    
    @tornado.web.authenticated
    def post(self, user_to_unfollow):
        """Updates the logged in user to not follow ``user_to_not_follow``."""
        
        this_user = self.current_user["user_name"]
        
        relationships_cf = self.column_family("Relationships")
        ordered_rels_cf = self.column_family("OrderedRelationships")
        user_metrics_cf = self.column_family("UserMetrics")
        
        # read the Relationship CF to see when it started
        row_key = (this_user, "following")
        columns = [
            user_to_unfollow
        ]
        try:
            rel_cols = relationships_cf.get(row_key, columns=columns)
        except (pycassa.NotFoundException):
            # not following the user. 
            self.redirect("/users/%(user_to_unfollow)s" % vars())
            return
        
        # Have {other_user_name : timestamp}
        following_started = rel_cols[user_to_unfollow]
        
        with pycassa.batch.Mutator(self.application.cass_pool) as batch:
            batch.write_consistency_level = cass_types.ConsistencyLevel.QUORUM
            
            # Delete from the Relationships CF
            row_key = (this_user, "following")
            columns = [
                user_to_unfollow
            ]
            batch.remove(relationships_cf, row_key, columns=columns)
            
            row_key = (user_to_unfollow, "followers")
            columns = [
                this_user
            ]
            batch.remove(relationships_cf, row_key, columns=columns)
            
            # Delete from OrderedRelationships CF
            row_key = (this_user, "following")
            columns = [
                (following_started, user_to_unfollow)
            ]
            batch.remove(ordered_rels_cf, row_key, columns=columns)
            
            row_key = (user_to_unfollow, "followers")
            columns = [
                (following_started, this_user),
            ]
            batch.remove(ordered_rels_cf, row_key, columns=columns)
        
        # Update the metrics
        row_key = user_to_unfollow
        user_metrics_cf.add(row_key, "followers", value=-1)
        
        row_key = this_user
        user_metrics_cf.add(row_key, "following", value=-1)
        
        
        self.redirect("/users/%(user_to_unfollow)s" % vars())
        return


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


class Logout(ControllerBase):
    
    def get(self):
        
        self.clear_cookie("user")
        self.redirect("/")
        return
        