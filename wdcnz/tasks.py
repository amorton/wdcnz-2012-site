"""Just put all the smarts in here"""

import logging 

import celery

import pycassa
from pycassa.cassandra import ttypes as cass_types


@celery.task()
def deliver_tweet(from_user, tweet_id, tweet_json):
    """Delivers the tweet with ``tweet_id`` to ``from_user``'s followers.
    """
    
    pool = get_cass_pool()
    relationships_cf = column_family(pool, "Relationships")
    user_timeline_cf = column_family(pool, "UserTimeline")
    tweet_delivery_cf = column_family(pool, "TweetDelivery")
    
    with pycassa.batch.Mutator(pool, queue_size=50) as batch:
        batch.write_consistency_level = cass_types.ConsistencyLevel.QUORUM
    
        row_key = (from_user, "followers")
        try:
            rel_cols = relationships_cf.get(row_key)
        except (pycassa.NotFoundException):
            rel_cols = {}
            
        for col_name, col_value in rel_cols.iteritems():
            # col name is user_name
            follower_user_name = col_name
            
            # Mark that we delivered the tweet to this user.
            row_key = int(tweet_id)
            columns = {
                str(follower_user_name) : ""
            }
            batch.insert(tweet_delivery_cf, row_key, columns)
            
            # Insert tweet into UserTimeline CF
            row_key = follower_user_name
            columns = {
                int(tweet_id) : str(tweet_json)
            }
            batch.insert(user_timeline_cf, row_key, columns)

    return
    

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Helpers

def get_cass_pool():
    return pycassa.ConnectionPool("wdcnz", ["localhost:9160"])

def column_family(cass_pool, name):
    return pycassa.ColumnFamily(cass_pool, name, 
        read_consistency_level=cass_types.ConsistencyLevel.QUORUM, 
        write_consistency_level=cass_types.ConsistencyLevel.QUORUM)