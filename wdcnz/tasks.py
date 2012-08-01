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
        def yield_followers():
            row_key = (from_user, "followers")
            try:
                
                # Page the followers list using column_start param
                rel_cols = relationships_cf.get(row_key, column_count=21)
                
                # Have {user_name : None}
                follower_names = rel_cols.keys()
                
                while follower_names:
                    # If we have 21 followers, there may be more.
                    if len(follower_names) == 21:
                        # Last col is the next start col
                        column_start = follower_names[-1]
                        # Do not yield the last col
                        follower_names = follower_names[:-1]
                    else:
                        # less than one page, do not get another page
                        column_start = ""
                        
                    for follower_name in follower_names:
                        yield follower_name
                    
                    # get next page ?
                    if column_start:
                        rel_cols = relationships_cf.get(row_key, 
                            column_start=column_start, column_count=21)
                        follower_names = rel_cols.keys()
                    else:
                        follower_names = []
                        
            except (pycassa.NotFoundException):
                pass
        
        
        for follower_user_name in yield_followers():
            
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
        # Would make many calls in real system, see above.
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
            batch.remove(user_timeline_cf, row_key, columns=columns)
            
            # Delete from TweetDelivery CF
            row_key = int(tweet_id)
            columns = [
                delivered_user_name
            ]
            batch.remove(tweet_delivery_cf, row_key, columns=columns)
    # Exit Batch
    return
    


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Helpers

def get_cass_pool():
    return pycassa.ConnectionPool("wdcnz", ["localhost:9160"])

def column_family(cass_pool, name):
    return pycassa.ColumnFamily(cass_pool, name, 
        read_consistency_level=cass_types.ConsistencyLevel.QUORUM, 
        write_consistency_level=cass_types.ConsistencyLevel.QUORUM)