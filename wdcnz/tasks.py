import logging 

import celery

import pycassa
from pycassa.cassandra import ttypes as cass_types

@celery.task()
def deliver_tweet(from_user, tweet_id, tweet_json):
    """Delivers the tweet with ``tweet_id`` to ``from_user``'s followers.
    """
    
    # Reference CFs
    pool = get_cass_pool()
    relationships_cf = column_family(pool, "Relationships")
    user_timeline_cf = column_family(pool, "UserTimeline")
    tweet_delivery_cf = column_family(pool, "TweetDelivery")
    
    with pycassa.batch.Mutator(pool, queue_size=50) as batch:
        batch.write_consistency_level = cass_types.ConsistencyLevel.QUORUM
        
        # Get list of followers from RelationshipsCF
        # Would do many get's in real life
        row_key = (from_user, "followers")
        try:
            rel_cols = relationships_cf.get(row_key)
        except (pycassa.NotFoundException):
            rel_cols = {}
            
        for col_name, col_value in rel_cols.iteritems():
            # col name is user_name
            follower_user_name = col_name
            
            # Mark that we delivered to this user in TweetDelivery CF
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
    # Exit Batch
    return

@celery.task()
def recall_tweet(tweet_id):
    """Removes the tweet with ``tweet_id`` time lines it was delivered to.
    """
    
    # Reference CFs
    pool = get_cass_pool()
    tweet_delivery_cf = column_family(pool, "TweetDelivery")
    user_timeline_cf = column_family(pool, "UserTimeline")
    
    with pycassa.batch.Mutator(pool, queue_size=50) as batch:
        batch.write_consistency_level = cass_types.ConsistencyLevel.QUORUM
        
        # Read who the tweet was delivered to
        # Would make many calls in real system.
        row_key = int(tweet_id)
        try:
            delivery_cols = tweet_delivery_cf.get(row_key)
        except (pycassa.NotFoundException):
            delivery_cols = {}
        # Have {user_name : None}
         
        for col_name in delivery_cols.keys():
            delivered_user_name = col_name
            
            # Delete from the UserTimeline CF
            row_key = delivered_user_name
            columns = [
                int(tweet_id)
            ]
            batch.remove(user_timeline_cf, row_key, columns)
            
            # Delete from TweetDelivery CF
            # (Checkpointing incase of failure...)
            row_key = int(tweet_id)
            columns = [
                delivered_user_name
            ]
            batch.remove(tweet_delivery_cf, row_key, columns)
            
        # Have now recalled from all users.
        # Delete the TweetDelivery CF row 
        row_key = int(tweet_id)
        batch.remove(tweet_delivery_cf, row_key)
    return
    


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Helpers

def get_cass_pool():
    return pycassa.ConnectionPool("wdcnz", ["localhost:9160"])

def column_family(cass_pool, name):
    return pycassa.ColumnFamily(cass_pool, name, 
        read_consistency_level=cass_types.ConsistencyLevel.QUORUM, 
        write_consistency_level=cass_types.ConsistencyLevel.QUORUM)