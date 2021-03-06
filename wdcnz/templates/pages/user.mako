<%inherit file="/base.mako"/>
<%namespace file="/components.mako" name="components" />

## User Details

<%block name="content">

<div class="row well">
    <div class="span8">
        <h1 class="span8">
            ${show_user["user_name"]}
            <p><small>${show_user.get("real_name")}</small></p>
        </h1>
    </div>
    <div class="span3">
        %if not is_current_user:
            <form id="frm_follow" method="POST">
                %if this_user_follows:
                    <button class="btn btn-primary pull-right btn-unfollow" formaction="/users/${show_user['user_name']}/not_followers" type="submit">Following</button>
                %endif
                %if not this_user_follows:
                    <button class="btn pull-right btn-follow" formaction="/users/${show_user['user_name']}/followers" type="submit">Follow</button>
                %endif
            </form>
            % if follows_this_user:
                <h6>${show_user.get("real_name", show_user["user_name"])} follows you.</h6>
            % endif 
        %endif
    </div>
</div>

<div class="row">
    <div class="span4">
        <ul class="nav nav-pills nav-stacked">
            <li class="active">
                <a href="#tweets" data-toggle="tab">Tweets&nbsp;<small>(${user_metrics.get("tweets", 0)})</small></a>
            </li>
            <li class="">
                <a href="#followers" data-toggle="tab">Followers&nbsp;<small>(${user_metrics.get("followers", 0)})</small></a>
            </li>
            <li class="">
                <a href="#following" data-toggle="tab">Following&nbsp;<small>(${user_metrics.get("following", 0)})</small></a>
            </li>
        </ul>
    </div>
  
    <div class="content-main span8">
        <div class="tab-content">
        
            <div class="tab-pane active" id="tweets">
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
                <div class="content-following">
                    <%components:user_list users="${following}" title="Following"/>
                </div>
            </div>
        </div>
    </div>
</div>
</%block>



<%block name="script_inline">
  <script>
    $(function () {
        $(".btn-unfollow").hover(
          function () {
            $(this).addClass("btn-danger")
            .removeClass("btn-primary")
            .text("Unfollow")
          }, 
          function () {
            $(this).addClass("btn-primary")
            .removeClass("btn-danger")
            .text("Following")
          }
        );
    });
  </script>
</%block>



