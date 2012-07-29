<%inherit file="/base.mako"/>
## Splash page for unknown users. 

<%block name="content">

<div class="row">
  <div class="span6">
    <h1>Welcome Back</h1>

    <form class="well" action="/login" method="post">
      <input type="text" class="span5" placeholder="User Name" name="user_name" />
      <input type="text" class="span5" placeholder="Password" name="user_password" />
      <div class="form-actions">
        <button type="submit" class="btn">Sign In</button>
    </div>
    </form>
  </div>

  <div class="span6">
    <h1>New User?</h1>
    <form class="well" action="/signup" method="post">
      <input type="text" class="span5" placeholder="User Name" name="user_name" />
      <input type="text" class="span5" placeholder="Password" name="password" />

      <input type="text" class="span5" placeholder="Real Name" name="real_name" />

      <div class="form-actions">
        <button type="submit" class="btn">Sign Up</button>
      </div>
    </form>
  </div>
</div>

</%block>
