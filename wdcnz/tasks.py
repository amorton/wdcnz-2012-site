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
    followers_cf = column_family(pool, "OrderedFollowers")
    user_timeline_cf = column_family(pool, "UserTimeline")
    
    with pycassa.batch.Mutator(pool, queue_size=50) as batch:
        batch.write_consistency_level = cass_types.ConsistencyLevel.QUORUM

        columns = {
            tweet_id : tweet_json
        }
    
        followers_row_key = from_user
        for col_name, _ in followers_cf.get(followers_row_key).iteritems():
            # col name is (timestamp, user_name)
            _, follower_user_name = col_name
            
            # Insert tweet into UserTimeline CF
            row_key = follower_user_name
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