<%inherit file="/base.mako"/>
<%namespace file="/components.mako" name="components" />

## Home page for a logged in user

<%block name="content">

<div class="row">
  <div class="span3">
    <h1>
        <a href="/users/${user["user_name"]}">${user.get("real_name", user["user_name"])}</a>
        <p><small>@${user["user_name"]}</small></p>
    </h1>
  </div>
  
  <div class="content-main span9">
    <div class="content-tweets">
        <%components:tweet_list title="${'Recent Tweets' if global_timeline else 'Tweets'}"/>
    </div>
  </div>
</div>
</%block>
