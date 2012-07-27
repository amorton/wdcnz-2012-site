<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>WDCNZ</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="">
    <meta name="author" content="">

    <!-- Le styles -->
    <link href="/static/css/bootstrap.css" rel="stylesheet">
    <style type="text/css">
      body {
        padding-top: 60px;
        padding-bottom: 40px;
      }
    </style>
    <link href="/static/css/bootstrap-responsive.css" rel="stylesheet">

    <!-- Le HTML5 shim, for IE6-8 support of HTML5 elements -->
    <!--[if lt IE 9]>
      <script src="http://html5shim.googlecode.com/svn/trunk/html5.js"></script>
    <![endif]-->
    <link href="/static/css/custom.css" rel="stylesheet">


    <!-- Le fav and touch icons -->
    <link rel="shortcut icon" href="/static/img/favicon.ico">
    <!-- <link rel="apple-touch-icon-precomposed" sizes="144x144" href="../assets/ico/apple-touch-icon-144-precomposed.png">
    <link rel="apple-touch-icon-precomposed" sizes="114x114" href="../assets/ico/apple-touch-icon-114-precomposed.png">
    <link rel="apple-touch-icon-precomposed" sizes="72x72" href="../assets/ico/apple-touch-icon-72-precomposed.png">
    <link rel="apple-touch-icon-precomposed" href="../assets/ico/apple-touch-icon-57-precomposed.png"> -->
  </head>

  <body>

    <div class="navbar navbar-fixed-top">
      <div class="navbar-inner">
        <div class="container">
          <a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </a>
          <a class="brand" href="#">WDCNZ</a>
          <div class="nav-collapse">
            <ul class="nav">
              <li class="active"><a href="#">Home</a></li>
              <li><a href="#about">About</a></li>
              <li><a href="#contact">Contact</a></li>
            </ul>
          </div><!--/.nav-collapse -->
          <ul class="nav pull-right">
            <a class="btn" data-toggle="modal" href="#modal_new_tweet"><i class="icon-pencil"></i></a>
          </ul>
        </div>
      </div>
    </div>
    
    % if error_message:
      <div class="alert alert-error">
        ${error_message}
      </div>
    % endif
    
    <div class="container">
      <%block name="content">
      </%block>
      
      <hr>

      <footer>
        <p>This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc/3.0/nz/">Creative Commons Attribution-NonCommercial 3.0 New Zealand License</a>.</p>
      </footer>

    </div> <!-- /container -->

    <!-- Le javascript
    ================================================== -->
    <!-- Placed at the end of the document so the pages load faster -->
    <script src="/static/js/jquery.js"></script>
    <script src="/static/js/bootstrap.min.js"></script>
    
    <div class="modal hide" id="modal_new_tweet">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">x</button>
        <h3>What's the word?</h3>
      </div>
      <div class="modal-body">
        <form id="frm_new_tweet" class="" action="/tweet" method="post">
          <textarea class="input-xxlarge" name="tweet_body" id="tweet_body" rows="3"></textarea>
        </form>
      </div>
      <div class="modal-footer">
        <button class="btn btn-primary" type="submit" form="frm_new_tweet">W.O.R.D. Up!</button>
      </div>
    </div>

  </body>
</html>
