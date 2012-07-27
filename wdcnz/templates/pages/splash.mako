<%inherit file="/base.mako"/>
## Splash page for unknown users. 

<%block name="content">

<div class="row">
  <div class="span4">
    <h1>Welcome Back -----></h1>
  </div>
  <div class="span4">
    <form class="well" action="/login" method="post">
      <input type="text" class="span3" placeholder="User Name" name="user_name">
      <input type="text" class="span3" placeholder="Password" name="user_password">
      <button type="submit" class="btn">Sign In</button>
    </form>
  </div>
</div>

<div class="row">
  <div class="span4">
    <h1>New User? --------></h1>
  </div>
  <div class="span4">
    <form class="well" action="/signup" method="post">
      <input type="text" class="span3" placeholder="User Name" name="new_user_name">
      <input type="text" class="span3" placeholder="Password" name="new_user_password">

      <input type="text" class="span3" placeholder="Real Name" name="new_user_realname">

      <button type="submit" class="btn">Sign Up</button>
    </form>
  </div>
</div>

</%block>
