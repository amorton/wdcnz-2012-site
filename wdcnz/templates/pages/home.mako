<%inherit file="/base.mako"/>
<%namespace file="/components.mako" name="components" />

## Home page for a logged in user

<%block name="content">

<div class="row">
  <div class="span3">
    <h1>LHS</h1>
  </div>
  
  <div class="content-main span9">
    <div class="content-header">
      <h2>Tweets</h2>
    </div>

    <div class="content-tweets">
        <%components:tweet_list />
    </div>
  </div>
</div>
</%block>
