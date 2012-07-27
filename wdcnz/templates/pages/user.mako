<%inherit file="/base.mako"/>
<%namespace file="/components.mako" name="components" />

## User Details

<%block name="content">

<div class="row well">
    <div class="span8">
        <h1 class="span8">
            ${user["user_name"]}
            <p><small>${user.get("real_name")}</small></p>
        </h1>
    </div>
    <div class="span3">
        <form id="frm_follow" method="POST" action="/users/${user['user_name']}/followers">
            <button class="btn btn-primary pull-right" type="submit">Follow</button>
        </form>
    </div>
</div>

<div class="row">
    <div class="span4">
        <ul class="nav nav-pills nav-stacked">
            <li class="active">
                <a href="#tweets" data-toggle="tab">Tweets</a>
            </li>
            <li class="">
                <a href="#followers" data-toggle="tab">Followers</a>
            </li>
            <li class="">
                <a href="#following" data-toggle="tab">Following</a>
            </li>
        </ul>
    </div>
  
    <div class="content-main span8">
        <div class="tab-content">
        
            <div class="tab-pane active" id="tweets">
                <div class="content-header">
                  <h2>Tweets</h2>
                </div>

                <div class="content-tweets">
                    <%components:tweet_list />
                </div>
            </div>

            <div class="tab-pane" id="followers">
                <div class="content-followers">
                    <%components:user_list users="${followers}" title="Followers"/>
                </div>
            </div>

            <div class="tab-pane" id="following">
                <div class="content-header">
                  <h2>Following</h2>
                </div>

                <div class="content-following">
                    bar
                </div>
            </div>
        </div>
    </div>
</div>
</%block>
